# """
# Seed the SQLite database with sample data for the "Reach staff" user.

# Run from the src/backend directory:
#     python seed.py
# """

# import json
# from sql_db import Database

# db = Database(create=False)

# # ---------------------------------------------------------------------------
# # User
# # ---------------------------------------------------------------------------

# db.insert(
#     "users",
#     [
#         "Reach staff",
#         "scrypt:32768:8:1$5fXSqKRIYoY9nuUp$0e3f5c9e152588e3da245c48117629ca9ffc128e810087ea960ee073c503c4858f5d663c1c53a18121f507231e0a5a58f769a7e295f9762677ef0b1efb94d506",
#         "",
#         1500,
#         350.0,
#         0.06,
#         None,  # week_schedule — populated automatically by check_new_week
#         json.dumps(
#             {
#                 "monday": 5,
#                 "tuesday": 5,
#                 "wednesday": 5,
#                 "thursday": 5,
#                 "friday": 5,
#                 "saturday": 5,
#                 "sunday": 5,
#             }
#         ),
#     ],
# )

# print("Seed complete.")
# print(f"  {len(db.select('users', 'all'))} user(s)")
