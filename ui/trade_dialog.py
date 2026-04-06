from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QMessageBox,
    QFrame, QSplitter,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from db import player_repo
from config import NPC_BUY_RATE


class TradeDialog(QDialog):
    """
    Dedicated shop dialog for trading with an NPC.
    Left panel: NPC's items for sale (buy).
    Right panel: Player's inventory (sell).
    """

    trade_complete = pyqtSignal()    # refresh sidebar after closing

    def __init__(self, npc: dict, player_id: int, parent=None):
        super().__init__(parent)
        self.npc       = npc
        self.player_id = player_id
        self.setWindowTitle(f"Trading with {npc['name']}")
        self.setMinimumSize(620, 440)
        self._build_ui()
        self._refresh()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Title
        title = QLabel(f"⚖  {self.npc['name']}'s Wares")
        title.setStyleSheet("color:#c9a84c; font-size:15px; font-weight:bold;")
        layout.addWidget(title)

        # Gold display
        self.lbl_gold = QLabel()
        self.lbl_gold.setStyleSheet("color:#22c55e; font-size:12px;")
        layout.addWidget(self.lbl_gold)

        # Splitter: NPC shop | Player inventory
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- NPC shop (left)
        left = QFrame()
        left.setObjectName("card")
        ll = QVBoxLayout(left)
        ll.addWidget(QLabel("🛒  For Sale"))
        self.shop_list = QListWidget()
        ll.addWidget(self.shop_list)
        self.btn_buy = QPushButton("Buy Selected")
        self.btn_buy.clicked.connect(self._buy_item)
        ll.addWidget(self.btn_buy)
        splitter.addWidget(left)

        # --- Player inventory (right)
        right = QFrame()
        right.setObjectName("card")
        rl = QVBoxLayout(right)
        rl.addWidget(QLabel("🎒  Your Inventory"))
        self.inv_list = QListWidget()
        rl.addWidget(self.inv_list)
        self.btn_sell = QPushButton("Sell Selected")
        self.btn_sell.clicked.connect(self._sell_item)
        rl.addWidget(self.btn_sell)
        splitter.addWidget(right)

        layout.addWidget(splitter)

        # Close
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

    # ── Refresh ───────────────────────────────────────────────────────────────

    def _refresh(self):
        player = player_repo.get_player(self.player_id)
        gold   = player["gold"] if player else 0
        self.lbl_gold.setText(f"◈ Your gold: {gold}")

        # Shop items
        self.shop_list.clear()
        for item in self.npc.get("shop_items", []):
            text  = f"{item['name']}  —  {item['price']} gold"
            entry = QListWidgetItem(text)
            entry.setData(Qt.ItemDataRole.UserRole, item)
            self.shop_list.addItem(entry)

        # Player inventory
        self.inv_list.clear()
        inventory = player_repo.get_inventory(self.player_id)
        for inv_item in inventory:
            sell_price = max(1, int(inv_item.get("properties", {}).get("value", 10) * NPC_BUY_RATE))
            text  = f"{inv_item['item_name']}  ×{inv_item['quantity']}  —  sells for {sell_price}g"
            entry = QListWidgetItem(text)
            entry.setData(Qt.ItemDataRole.UserRole, {**inv_item, "sell_price": sell_price})
            self.inv_list.addItem(entry)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _buy_item(self):
        selected = self.shop_list.currentItem()
        if not selected:
            return
        item   = selected.data(Qt.ItemDataRole.UserRole)
        price  = item.get("price", 999)
        player = player_repo.get_player(self.player_id)
        if player["gold"] < price:
            QMessageBox.warning(self, "Not enough gold",
                                f"You need {price} gold but only have {player['gold']}.")
            return
        player_repo.update_player_stats(self.player_id, gold=player["gold"] - price)
        player_repo.add_item(
            self.player_id,
            item["name"],
            item.get("type", "misc"),
            1,
            item.get("properties", {}),
        )
        self._refresh()
        self.trade_complete.emit()

    def _sell_item(self):
        selected = self.inv_list.currentItem()
        if not selected:
            return
        item       = selected.data(Qt.ItemDataRole.UserRole)
        sell_price = item["sell_price"]
        removed    = player_repo.remove_item(self.player_id, item["item_name"], 1)
        if removed:
            player = player_repo.get_player(self.player_id)
            player_repo.update_player_stats(self.player_id, gold=player["gold"] + sell_price)
            self._refresh()
            self.trade_complete.emit()
