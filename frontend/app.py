import logging

from flask import Flask, render_template, request, redirect, session, flash
from backend_client import BackendClient
import json
from kafka import KafkaProducer


# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',  # Update with your Kafka broker address
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)


# Explicit logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()  # Output logs to console
    ]
)
app = Flask(__name__)
app.secret_key = "supersecretkey"

# Initialize backend client
client = BackendClient()


def get_user_session():
    """Retrieve user session details."""
    logging.info("Retrieving user session")
    return session.get("user")


@app.route("/", methods=["GET", "POST"])
def register_page():
    """
    User Registration Page.
    """
    logging.info("User Registration Page")
    logging.info(f'Request method: {request.method}')
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        name = request.form.get("name")
        category = request.form.get("category")
        city = request.form.get("city")

        try:
            preferences = {"category": [cat.strip() for cat in category.split(",")], "city": city.strip()}
            preferences_json = json.dumps(preferences)
            logging.info(f"Preferences JSON: {preferences_json}")

            # Call backend API
            response = client.register_user(email, password, name, preferences_json)
            logging.info(f"User registration response: {response}")

            # Store session data and redirect to home
            session["user"] = {"email": email, "name": name, "preferences": preferences}
            logging.info(f"User session response: {session.get('user')}")

            return redirect("/home")
        except Exception as e:
            return render_template("register.html", error=f"Error during registration: {str(e)}")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    User login page.
    """
    logging.info("Login Page")
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        logging.info(f"Login attempt for email: {email}")

        # Call the backend login_user method
        response = client.login_user(email, password)
        logging.info(f"Login response: {response}")

        if not response.get("success"):
            error_message = response.get("error", "Unknown error during login")
            logging.error(f"Login failed: {error_message}")
            flash(f"Error: {error_message}", "danger")
            return redirect("/login")

        # Extract token and user details
        user_data = response["response"]
        try:
            preferences = json.loads(user_data.get("preferences", "{}"))
        except json.JSONDecodeError:
            logging.error("Failed to decode preferences JSON")
            preferences = {}

        session["user"] = {
            "email": email,
            "token": user_data.get("token"),
            "user_id": user_data.get("user_id"),
            "preferences": preferences,  # Store deserialized preferences
            "name": user_data.get("name"),
        }
        logging.info(f"User logged in: {session['user']}")
        return redirect("/login_recommendations")

    return render_template("login.html")

@app.route("/home", methods=["GET"])
def home():
    # Retrieve user from session
    user = get_user_session()

    if not user:
        logging.warning("No user session found. Redirecting to login.")
        return redirect("/login")  # Redirect to login if no user session is found

    # Log the current user session data
    logging.info(f"User session data: {user}")

    # Ensure `registered` is part of the user dictionary for template rendering
    user.setdefault("registered", True)

    return render_template(
        "home.html",
        user=user,  # Pass user details to the template
    )

@app.route("/recommendations", methods=["POST", "GET"])
def recommendations():
    logging.info("Recommendations Page")
    user = get_user_session()

    if not user:
        logging.warning("No user session found. Redirecting to login.")
        return redirect("/login")

    preferences = user["preferences"]["category"]
    city = user["preferences"]["city"]

    try:
        response = client.get_recommendations(preferences, city.strip())
        if response["success"]:
            recommendations = response["response"].recommendations
            logging.info(f"Recommendations fetched: {recommendations}")
            return render_template(
                "recommendations.html", recommendations=recommendations, user=user
            )
        else:
            logging.error(f"Error fetching recommendations: {response['error']}")
            return render_template("recommendations.html", recommendations=[], user=user)
    except Exception as e:
        logging.error(f"Error during recommendation fetching: {str(e)}")
        return render_template("recommendations.html", recommendations=[], user=user)

@app.route("/login_recommendations", methods=["GET", "POST"])
def login_recommendations():
    """
    Page displayed after user login.
    Shows current preferences and a form to update preferences.
    """
    # Retrieve user from session
    user = get_user_session()

    if not user:
        logging.warning("No user session found. Redirecting to login.")
        return redirect("/login")  # Redirect to login if no user session is found

    logging.info(f"User session data: {user}")

    # Handle preference updates
    if request.method == "POST":
        category = request.form.get("category")
        city = request.form.get("city")

        try:
            # Validate and update preferences
            preferences = {"category": [cat.strip() for cat in category.split(",")], "city": city.strip()}
            user["preferences"] = preferences

            # Save updated preferences in the session
            session["user"] = user

            # Log updated preferences
            logging.info(f"Updated preferences: {preferences}")
            flash("Preferences updated successfully!", "success")
        except Exception as e:
            logging.error(f"Error updating preferences: {str(e)}")
            flash("Failed to update preferences. Please try again.", "danger")

    return render_template(
        "login_recommendations.html",
        user=user,  # Pass user details to the template
    )
#
# @app.route("/update_preferences", methods=["POST", "GET"])
# def update_preferences():
#     user = get_user_session()
#
#     if not user:
#         return redirect("/login")
#
#     if request.method == "POST":
#         category = request.form.get("category")
#         city = request.form.get("city")
#
#         try:
#             # Update preferences in the backend
#             response = client.update_preferences(
#                 user_id=user["user_id"],
#                 category=[cat.strip() for cat in category.split(",")],
#                 city=city.strip()
#             )
#             logging.info(f"Updated preferences: {response}")
#
#             if response["success"]:
#                 flash("Preferences updated successfully.", "success")
#                 session["user"]["preferences"] = {"category": category, "city": city}
#                 return redirect("/recommendations")
#             else:
#                 flash(f"Failed to update preferences: {response['error']}", "danger")
#         except Exception as e:
#             flash(f"An error occurred: {str(e)}", "danger")
#
#     return render_template("login_recommendations.html")

@app.route("/update_preferences", methods=["POST", "GET"])
def update_preferences():
    user = get_user_session()

    # Redirect to login if user session is missing
    if not user:
        return redirect("/login")

    if request.method == "POST":
        # Get category and city from the form
        category = request.form.get("category")
        city = request.form.get("city")

        try:
            # Clean and prepare category list
            category_list = [cat.strip() for cat in category.split(",")]
            city_cleaned = city.strip()

            # Update preferences in the backend
            response = client.update_preferences(
                user_id=user["user_id"],
                category=category_list,
                city=city_cleaned
            )
            logging.info(f"Updated preferences: {response}")

            # Publish to Kafka topic if update is successful
            if response["success"]:
                message = {
                    "user_id": user["user_id"],
                    "preferences": {
                        "category": category_list,
                        "city": city_cleaned
                    }
                }
                producer.send('preferences_update', message)
                producer.flush()
                logging.info(f"Published preferences update to Kafka: {message}")

                # Update session and redirect
                session["user"]["preferences"] = {
                    "category": category_list,
                    "city": city_cleaned
                }
                flash("Preferences updated successfully.", "success")
                return redirect("/recommendations")
            else:
                flash(f"Failed to update preferences: {response['error']}", "danger")
        except Exception as e:
            # Handle general errors
            logging.error(f"Error in update_preferences: {str(e)}")
            flash(f"An error occurred: {str(e)}", "danger")

    # Render the login_recommendations page with the current user context
    return render_template("login_recommendations.html", user=user)

@app.route("/logout", methods=["GET"])
def logout():
    """Logout and clear session."""
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    port = 5000
    print(f"Running on http://127.0.0.1:{port}")
    app.run(debug=True, port=port)