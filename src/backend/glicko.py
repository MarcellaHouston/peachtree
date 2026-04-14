from sql_db import Database
import math


class Glicko:   
    def __init__(self, rating: int, RD: float, volatility: float, tasks: list):
        self.SYSTEM_CONSTANT = 0.5
        self.SCALE = 173.7178
        self.volatility = volatility
        self.user_rating, self.user_RD = self.to_glicko_scale(rating, RD)

        self.tasks = []
        for task in tasks:
            task_rating, task_RD = self.to_glicko_scale(task["task_rating"], task["task_RD"])
            self.tasks.append({
                "rating": task_rating,
                "RD": task_RD,
                "score": task["task_score"] # 0 if user failed, 1 if user completed
            })
    

    def to_glicko_scale(self, rating: int, RD: float) -> tuple:
        mu = (rating - 1500) / self.SCALE
        phi = RD / self.SCALE
        return mu, phi

    def from_glicko_scale(self, mu: float, phi: float) -> tuple:
        rating = (mu * self.SCALE) + 1500
        RD = phi * self.SCALE
        return rating, RD

    def g_phi(self, phi: float) -> float:
        expr = math.sqrt(1 + ((3 * pow(phi, 2)) / pow(math.pi, 2)))
        return 1.0 / expr
    
    def e_func(self, mu: float, mu_j: int, phi_j: float) -> float:
        g_phi_j = self.g_phi(phi_j)
        expr = 1.0 + math.exp((-g_phi_j) * (mu - mu_j))
        return 1.0 / expr
    
    def variance_piece(self, mu: float, mu_j: float, phi_j: float) -> float:
        g_phi_j = self.g_phi(phi_j)
        e_func_result = self.e_func(mu, mu_j, phi_j)
        expr = pow(g_phi_j, 2) * e_func_result * (1.0 - e_func_result)
        return expr

    def calc_variance(self) -> float:
        varianceSum = 0
        for task in self.tasks:
            new_piece = self.variance_piece(self.user_rating, task["rating"], task["RD"])
            varianceSum = varianceSum + new_piece
        return 1.0 / varianceSum
    
    def rating_piece(self, mu: float, mu_j: float, phi_j: float, s_j: int) -> float:
        g_phi_j = self.g_phi(phi_j)
        e_func_result = self.e_func(mu, mu_j, phi_j)
        expr = g_phi_j * (s_j - e_func_result)
        return expr

    def rating_improvement(self, variance: float) -> float:
        improvement = 0
        for task in self.tasks:
            new_piece = self.rating_piece(self.user_rating, task["rating"], task["RD"], task["score"])
            improvement = improvement + new_piece
        return (variance * improvement)
    
    def f_x(self, x: float, delta: float, variance: float, phi: float, a: float) -> float:
        numerator = math.exp(x) * (pow(delta, 2) - pow(phi, 2) - variance - math.exp(x))
        denominator = pow(phi, 2) + variance + math.exp(x)
        denominator = 2.0 * pow(denominator, 2)
        first_term = numerator / denominator

        second_term = (x - a) / pow(self.SYSTEM_CONSTANT, 2)
        return first_term - second_term

    def calc_new_volatility(self, delta: float, variance: float) -> float:
        # Set initial values according to Glicko-2 iterative algorithm
        A_true = math.log(pow(self.volatility, 2))
        A = A_true
        epsilon = 0.000001
        delt_sq = pow(delta, 2)
        phi_sq = pow(self.user_RD, 2)
        B = 0.0
        if delt_sq > phi_sq + variance:
            B = math.log(delt_sq - phi_sq - variance)
        else:
            k = 1
            while self.f_x(A - (k * self.SYSTEM_CONSTANT), delta, variance, self.user_RD, A) < 0:
                k = k + 1
            B = A - (k * self.SYSTEM_CONSTANT)
        # Assign f(A) and f(B)
        f_a = self.f_x(A, delta, variance, self.user_RD, A)
        f_b = self.f_x(B, delta, variance, self.user_RD, A)
        # Last iteration to find new volatility
        while abs(B - A) > epsilon:
            c_numerator = (A - B) * f_a
            c_denominator = f_b - f_a
            C = A + (c_numerator / c_denominator)
            f_c = self.f_x(C, delta, variance, self.user_RD, A_true)
            if (f_c * f_b) <= 0:
                A = B
                f_a = f_b
            else:
                f_a = f_a / 2.0
            B = C
            f_b = f_c
        new_volatility = math.exp(A / 2.0)
        return new_volatility
    
    def pre_rating_val(self, sigma: float) -> float:
        return math.sqrt(pow(self.user_RD, 2) + pow(sigma, 2))
    
    def update_vals(self, pre_rating: float, variance: float) -> tuple:
        new_RD = 1.0 / math.sqrt((1.0 / pow(pre_rating, 2)) + (1.0 / variance))

        rd_sum = 0
        for task in self.tasks:
            g_phi_j = self.g_phi(task["RD"])
            e_phi_j = self.e_func(self.user_rating, task["rating"], task["RD"])
            rd_sum = rd_sum + (g_phi_j * (task["score"] - e_phi_j))

        new_rating = self.user_rating + (pow(new_RD, 2) * rd_sum)
        return new_rating, new_RD
        

    def perform_glicko(self) -> tuple:
        # Compute estimated variance of user's rating based only on "match" outcomes
        est_var = self.calc_variance()

        # Compute delta, the estimated improvement in rating
        delta = self.rating_improvement(est_var)

        # Determine new value of the volatility
        new_volatility = self.calc_new_volatility(delta, est_var)

        # Update rating deviation (RD) to new pre-rating period value
        pre_rating_value = self.pre_rating_val(new_volatility)

        # Calculate user's new rating and RD values
        new_rating, new_RD = self.update_vals(pre_rating_value, est_var)

        # Convert rating and RD back to original scale
        scaled_rating, scaled_RD = self.from_glicko_scale(new_rating, new_RD)

        return int(scaled_rating), scaled_RD, new_volatility