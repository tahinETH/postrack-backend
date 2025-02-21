from dotenv import load_dotenv
import os

load_dotenv()

class EnvConfig:
    def __init__(self):
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
        
        if self.ENVIRONMENT == "prod":
            self.DB_PATH = os.getenv("DB_PATH_PROD") 
            self.CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY_PROD")
            self.CLERK_WEBHOOK_SECRET = os.getenv("CLERK_WEBHOOK_SECRET_PROD")
            self.STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY_PROD")
            self.STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY_PROD")
           
        else:
            self.DB_PATH = os.getenv("DB_PATH_LOCAL")
            self.CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY_LOCAL")
            self.CLERK_WEBHOOK_SECRET = os.getenv("CLERK_WEBHOOK_SECRET_LOCAL")
            self.STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY_LOCAL")
            self.STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY_LOCAL")

# Create an instance of the config
config = EnvConfig()