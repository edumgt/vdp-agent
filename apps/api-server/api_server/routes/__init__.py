from . import companies, dart, journal, ml, reports, vouchers


def register_routes(app):
    app.register_blueprint(companies.bp)
    app.register_blueprint(journal.bp)
    app.register_blueprint(vouchers.bp)
    app.register_blueprint(reports.bp)
    app.register_blueprint(ml.bp)
    app.register_blueprint(dart.bp)
