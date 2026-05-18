from fastapi import FastAPI
from config import settings
from database.session import Base, engine
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server Startup")
    Base.metadata.create_all(bind=engine)
    yield
    print("Server Shutdown")

def create_app():
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.PROJECT_VERSION,
        lifespan=lifespan
    )

    from apis import auth as auth_router
    from apis import users as user_router
    from apis import companies as company_router
    from apis import emails as email_router


    @app.get("/", tags=["Root"])
    def read_root():
        return {"message": "Welcome to the AI-Assisted Smart Job Outreach System",
                "/docs" : "For interactive Swagger UI",
                "/redoc" : "For interactive ReDoc UI"
                }
    
    app.include_router(auth_router.router, tags=["Authentication"])
    app.include_router(user_router.router, tags=["Users"])
    app.include_router(company_router.router, tags=["Companies"])
    app.include_router(email_router.router, tags=["Emails"])
    
    return app

app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)