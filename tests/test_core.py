import unittest
from decimal import Decimal
from pathlib import Path
from app.core import Store, installments, sale_price

class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.store = Store(Path(__file__).resolve().parents[1])
    def test_stock(self): self.assertTrue(all(p.status == "active" and p.stock > 0 for p in self.store.search_products()))
    def test_pix_is_not_stacked(self):
        product_id = next(pid for pid, promo in self.store.promotions.items() if promo.active)
        p = self.store.products[product_id]; promo = self.store.promotions[product_id]
        result = sale_price(p, promo, "pix")
        self.assertFalse(result["pix_stacked"])
        self.assertEqual(result["current_price"], result["promotion_price"])
    def test_installment_threshold(self): self.assertFalse(installments(Decimal("49"), 3)["eligible"])
    def test_privacy(self): self.assertFalse(self.store.get_order(1)["authorized"])
    def test_evidence_has_source_metadata(self): self.assertTrue(all({"document", "section", "page"} <= set(x) for x in self.store.policy_search("pix")))

if __name__ == "__main__": unittest.main()
