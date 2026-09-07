from fastapi import FastAPI

from app.routes import admin_routes, auth_routes, paper_routes, user_routes

app = FastAPI(title="ScholarLink API", version="0.1.0")

app.include_router(auth_routes.router)
app.include_router(admin_routes.router)
app.include_router(user_routes.router)
app.include_router(paper_routes.router)


@app.get("/health", tags=["meta"])
def health_check():
    return {"status": "ok"}
