"""
Our secret sauce algorithm is a variation of the Glicko-2 algorithm created by Professor
Mark E. Glickman. Link to his paper --> https://www.glicko.net/glicko/glicko2.pdf

The players in the Glicko-2 system in the context of Reach are users and tasks. Matches are
simulated between the players and tasks. If the user completes the task, the user "wins" the match.
If the user fails to complete the task, the task "wins" and the user "loses". In our system, tasks
never gain or lose rating after their creation, as we are more concerned about measuring the user's
progress rather than the tasks. 

Every "player" has a rating, a rating deviation (RD), and a volatility measure. The volatility
parameter measures a player's degree of expected fluctuation. If volatility is low, then the
player is expected to perform consistently around their rating (completing tasks with rating at
or below the user's rating and failing tasks above their rating). If volatility is high, then the
player has had some erratic results (inconsistent with their rating). The rating deviation
represents helps summarize a user's strength as an interval. For example, with a rating of 1200
and a rating deviation (RD) of 50, the user's strength interval would be 1150-1250. Thus, a low
RD indicates a higher degree of confidence in a user's rating, and a high RD indicates skepticism,
typically in the case of new players.

To apply the rating algorithm, a collection of "games" played during a rating period is treated
simultaneously. In the case of Reach, this rating period is every day, with the collection of "games"
corresponding to the tasks that the user has in their daily schedule. The user's rating, RD, and
volatility values at the start of the day are used in the Glicko calculation, which then updates
and stores them in Reach's database to be used the next day.

The Glicko-2 scale that calculations are performed on are different from the default Glicko scale.
Ratings and RDs are scaled to Glicko-2 during the algorithm, and scaled back to Glicko once all
calculations are done. Glicko-2 also includes a system constant, which constrains the change in 
volatility over time. Reach's system constant is set at 0.5, which is fairly low. What this does
is ensure that users don't undergo extreme changes in their rating based onimprobable results, like
completing tasks with ratings way above thier own, or failing tasks with ratings much lower than
their own.

For new users, the default rating is set at 1500, the RD is set at 350.0, and the volatility is set
at 0.06. 
"""


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
            # Scale task rating and RD to Glicko-2 scale
            task_rating, task_RD = self.to_glicko_scale(task["task_rating"], task["task_RD"])
            self.tasks.append({
                "rating": task_rating,
                "RD": task_RD,
                "score": task["task_score"] # 0 if user failed, 1 if user completed
            })
    

    def to_glicko_scale(self, rating: int, RD: float) -> tuple:
        # Scale rating and RD to Glicko-2 scale
        mu = (rating - 1500) / self.SCALE
        phi = RD / self.SCALE
        return mu, phi

    def from_glicko_scale(self, mu: float, phi: float) -> tuple:
        #  Scale mu and phi back to normal Glicko scale
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
        # Helper function for calc_variance()
        g_phi_j = self.g_phi(phi_j)
        e_func_result = self.e_func(mu, mu_j, phi_j)
        expr = pow(g_phi_j, 2) * e_func_result * (1.0 - e_func_result)
        return expr

    def calc_variance(self) -> float:
        # Compute estimated variance of the user's rating based on their "game outcomes"
        # or on their failures and completions of the day's tasks
        varianceSum = 0
        for task in self.tasks:
            new_piece = self.variance_piece(self.user_rating, task["rating"], task["RD"])
            varianceSum = varianceSum + new_piece
        return 1.0 / varianceSum
    
    def rating_piece(self, mu: float, mu_j: float, phi_j: float, s_j: int) -> float:
        # Helper function for rating_improvement()
        g_phi_j = self.g_phi(phi_j)
        e_func_result = self.e_func(mu, mu_j, phi_j)
        expr = g_phi_j * (s_j - e_func_result)
        return expr

    def rating_improvement(self, variance: float) -> float:
        # Calculate delta, the estimated improvement of rating by comparing the
        # pre-period rating to the performance rating based on "game" outcomes
        # (task completions and failures)
        improvement = 0
        for task in self.tasks:
            new_piece = self.rating_piece(self.user_rating, task["rating"], task["RD"], task["score"])
            improvement = improvement + new_piece
        return (variance * improvement)
    
    def f_x(self, x: float, delta: float, variance: float, phi: float, a: float) -> float:
        # Helper function for calc_new_volatility()
        numerator = math.exp(x) * (pow(delta, 2) - pow(phi, 2) - variance - math.exp(x))
        denominator = pow(phi, 2) + variance + math.exp(x)
        denominator = 2.0 * pow(denominator, 2)
        first_term = numerator / denominator

        second_term = (x - a) / pow(self.SYSTEM_CONSTANT, 2)
        return first_term - second_term

    def calc_new_volatility(self, delta: float, variance: float) -> float:
        """Calculate the new volatility value"""
        # Set initial values according to Glicko-2 iterative algorithm.
        # A_true is a constant value that will be kept throughout the calculation.
        # A is initialized to A_true, but will change throughout the iterations
        A_true = math.log(pow(self.volatility, 2))
        A = A_true
        # epsilon is the convergence tolerance
        epsilon = 0.000001
        delt_sq = pow(delta, 2)
        phi_sq = pow(self.user_RD, 2)
        # A and B are used to bracket ln(variance^2). They are used to ensure that
        # the algorithm does converge to a new volatility value
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
        # Iteration to find new volatility.
        # This narrows the bracket of ln(variance^2) until the algorithm converges
        # on a new volatility value
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
        # Helper function for perform_glicko(). sigma should be the new volatility
        # value calculated in calc_new_volatility()
        return math.sqrt(pow(self.user_RD, 2) + pow(sigma, 2))
    
    def update_vals(self, pre_rating: float, variance: float) -> tuple:
        # Calculate and update the new rating and RD values for the user
        new_RD = 1.0 / math.sqrt((1.0 / pow(pre_rating, 2)) + (1.0 / variance))

        rd_sum = 0
        for task in self.tasks:
            g_phi_j = self.g_phi(task["RD"])
            e_phi_j = self.e_func(self.user_rating, task["rating"], task["RD"])
            rd_sum = rd_sum + (g_phi_j * (task["score"] - e_phi_j))

        new_rating = self.user_rating + (pow(new_RD, 2) * rd_sum)
        return new_rating, new_RD
        

    def perform_glicko(self) -> tuple:
        # Perform the Glicko algorithm in its entirety
        # The calculation of task ratings and the conversion of user and task data
        # to Glicko-2 scaling is done in __init__

        # If no matches were played over rating period, just update RD based on current RD and volatility
        if not self.tasks:
            new_RD = math.sqrt(pow(self.user_RD, 2) + pow(self.volatility, 2))
            scaled_rating, scaled_RD = self.from_glicko_scale(self.user_rating, new_RD)
            return int(scaled_rating), scaled_RD, self.volatility

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

        # Convert rating and RD back to Glicko scale
        scaled_rating, scaled_RD = self.from_glicko_scale(new_rating, new_RD)

        return round(scaled_rating), scaled_RD, new_volatility