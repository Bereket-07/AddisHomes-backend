import logging
import os
from flask import Flask, jsonify, request, send_file, Response
from flask_cors import CORS

from src.utils.config import settings
from src.utils.exceptions import RealEstatePlatformException, NotFoundError
from src.app.startup import user_use_cases, property_use_cases

# Import Blueprints
from src.controllers.admin_controller import admin_bp
from src.controllers.auth_controller import auth_bp
from src.controllers.property_controller import property_bp, car_bp

# Helpers
import io

logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    # CORS
    frontend_origin = getattr(settings, 'FRONTEND_ORIGIN', "http://localhost:5173")
    service_origin = settings.WEB_APP_URL if hasattr(settings, 'WEB_APP_URL') and settings.WEB_APP_URL else None
    allowed_origins = [frontend_origin]
    if service_origin:
        allowed_origins.append(service_origin)
        
    CORS(app, resources={r"/*": {"origins": "*"}}) # Using * for now as requested/easy debugging, can refine
    
    # Register Blueprints
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(property_bp)
    app.register_blueprint(car_bp) # Registered separately even though defined in same file
    
    # Error Handlers
    @app.errorhandler(RealEstatePlatformException)
    def handle_platform_exception(error):
        status_code = 500
        if isinstance(error, NotFoundError):
            status_code = 404
        return jsonify({"detail": error.message}), status_code

    @app.errorhandler(404)
    def handle_404(error):
        return jsonify({"detail": "Not Found"}), 404

    @app.errorhandler(500)
    def handle_500(error):
        return jsonify({"detail": "Internal Server Error"}), 500

    # Health Check
    @app.route("/", methods=["GET"])
    def health_check():
        return jsonify({"status": "ok", "project": settings.PROJECT_NAME, "version": "1.0.0 (Flask)"})

    # Startup logic
    with app.app_context():
        # Initialize admin user if needed (sync)
        try:
            user_use_cases.initialize_admin_user()
            logger.info("Admin init check complete.")
        except Exception as e:
            logger.error(f"Failed to initialize admin: {e}")

    # Image Serving
    @app.route("/images/<image_id>", methods=["GET"])
    def serve_image(image_id):
        repo_for_images = property_use_cases.repo
        if not hasattr(repo_for_images, 'get_image_blob'):
            return jsonify({"detail": "Image serving not available"}), 404
        
        try:
            record = repo_for_images.get_image_blob(image_id)
            if not record:
                return jsonify({"detail": "Image not found"}), 404
            
            content_type = record.get('content_type', 'application/octet-stream')
            data = record.get('data')
            
            return send_file(
                io.BytesIO(data),
                mimetype=content_type,
                as_attachment=False,
                download_name=f"{image_id}" 
            )
        except Exception as e:
            logger.error(f"Error serving image {image_id}: {e}")
            return jsonify({"detail": "Internal Server Error"}), 500

    return app

app = create_app()
application = app # For specific WSGI servers looking for 'application'

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)