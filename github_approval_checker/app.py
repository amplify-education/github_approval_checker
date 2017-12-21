"""Contains all of of the functions mapping to operationIds for the API, as well
as a few helper functions."""
import connexion
from flask_cors import CORS


app = connexion.FlaskApp(__name__, specification_dir='./specs/')
app.add_api('swagger.yml')

# Configure cross origin request sources.
CORS(
    app.app,
)

if __name__ == '__main__':
    app.run(port=8080)
