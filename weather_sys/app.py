"""weatherdemo Flask application entry point."""

if __package__:
    from .backend import create_app
else:  # 支持 python weather_sys/app.py 直接启动
    from backend import create_app


app = create_app()


if __name__ == "__main__":
    app.run(
        host=app.config["FLASK_HOST"],
        port=app.config["FLASK_PORT"],
        debug=app.config["FLASK_DEBUG"],
    )
