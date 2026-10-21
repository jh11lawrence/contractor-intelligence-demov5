import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import TABLES,load,analyse,comparison,tested_patterns,customer_invoices,invoices

class TestV5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(__file__).resolve().parents[1]/'data'
        cls.f=load({name:(root/f'{name}.csv').read_bytes() for name in TABLES})
        cls.jobs,_=analyse(cls.f)
        cls.completed=cls.jobs[(cls.jobs.Status=='Completed')&cls.jobs.CompleteDirectRecords]
    def test_comparison_totals_reconcile(self):
        for dimension in ('JobType','Customer','Estimator'):
            with self.subTest(dimension=dimension):
                group=comparison(self.completed,dimension)
                self.assertEqual(group.Jobs.sum(),len(self.completed))
                self.assertAlmostEqual(group.JobValue.sum(),self.completed.Revenue.sum(),places=5)
                self.assertAlmostEqual(group.Contribution.sum(),self.completed.RecordedContribution.sum(),places=5)
    def test_loss_count(self):
        g=comparison(self.completed,'Customer')
        self.assertEqual(g.LossJobs.sum(),(self.completed.RecordedContribution<0).sum())
    def test_patterns_adjusted_p(self):
        for x in tested_patterns(self.completed,'JobType'):
            self.assertGreaterEqual(x['AdjustedP'],x['PValue']-1e-10)
            self.assertLessEqual(x['AdjustedP'],1)
    def test_invoice_customer_totals(self):
        invoice=invoices(self.f,'2026-10-21')
        clients=customer_invoices(self.f,'2026-10-21')
        self.assertAlmostEqual(clients.InvoicedNet.sum(),invoice.NetAmount.sum(),places=5)
    def test_direct_contribution(self):
        j=self.completed
        self.assertAlmostEqual((j.Revenue-j.RecordedDirectCost-j.RecordedContribution).abs().max(),0,places=6)
if __name__=='__main__':unittest.main()
