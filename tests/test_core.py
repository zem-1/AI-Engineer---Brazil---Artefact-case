import os, unittest
from decimal import Decimal
from pathlib import Path
from app.core import Store, installments, sale_price
from app.postgres import policy_chunks
from app.tools import call_tool, TOOL_NAMES
from app.agent import run_agent

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
    def test_policy_chunk_has_source_hash(self):
        chunks = policy_chunks("Heading\nPIX is not stackable\fReturns in seven days", "policy.pdf")
        self.assertEqual([c["page"] for c in chunks], [1, 2])
        self.assertTrue(all(c["source_hash"] for c in chunks))
    def test_tool_registry_rejects_arbitrary_sql(self):
        with self.assertRaises(ValueError): call_tool(self.store, "execute_sql", {"query": "DROP TABLE products"})
    def test_tool_registry_is_bounded(self): self.assertNotIn("execute_sql", TOOL_NAMES)
    def test_mock_agent_is_available_without_credentials(self):
        os.environ["LLM_PROVIDER"] = "mock"
        result = run_agent(self.store, "Tem violão disponível até R$ 700?")
        self.assertIn("search_products", result["tools"])
    def test_policy_intent_prefers_defect(self):
        self.assertEqual(self.store.policy_search("troca por defeito")[0]["section"], "defects")
    def test_order_status_is_customer_facing_ptbr(self):
        from app.core import respond
        self.assertIn("entregue", respond(self.store, "Qual o status do pedido 1?", "3")["answer"])

if __name__ == "__main__": unittest.main()
