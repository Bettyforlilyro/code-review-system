from code_review_app import CodeReviewApp


def init_app(app: CodeReviewApp):
    """
    初始化app，这个包中的初始化是注册所有蓝图路由
    """
    from flask_cors import CORS

    from api.gateway import bp as gateway_bp
    from api.services import bp as services_bp

    CORS(
        gateway_bp,
        allow_headers=[
            "Content-Type",
            "Authorization",
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Headers",
            "Access-Control-Allow-Methods",
            "Access-Control-Allow-Credentials",
            "X-App-Code"
        ],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )
    app.register_blueprint(gateway_bp)

    CORS(
        services_bp,
        allow_headers=[
            "Content-Type",
            "Authorization",
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Headers",
            "Access-Control-Allow-Methods",
            "Access-Control-Allow-Credentials",
            "X-App-Code"
        ],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )
    app.register_blueprint(services_bp)


