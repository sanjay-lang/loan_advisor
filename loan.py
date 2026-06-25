class Loan:
    def __init__(self, bank_name, principal, rate, tenure):
        self.bank_name = bank_name
        self.principal = principal
        self.rate = rate
        self.tenure = tenure

    def calculate_emi(self):
        monthly_rate = self.rate / (12 * 100)
        months = self.tenure * 12

        if monthly_rate == 0:
            return self.principal / months

        emi = (
            self.principal
            * monthly_rate
            * (1 + monthly_rate) ** months
        ) / (
            (1 + monthly_rate) ** months - 1
        )

        return emi
