

# Owner Minte Restaurant Backed
# Run: uvicorn main:app --reload  
# Run: uvicorn owner_menu:app --host 0.0.0.0 --port 8000
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import json
import os
import time


# ============================================================
# APP
# ============================================================
app = FastAPI(title="Minte Restaurant Owner API", version="1.0.0")

# ============================================================
# CORS
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# PATHS
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CUSTOMER_JSON_PATH = os.path.join(BASE_DIR, "minte_hotel_digital_menu.json")
#OWNER_CONFIG_PATH = os.path.join(BASE_DIR, "owner_hotel_order_config.json")

IMAGES_DIR = os.path.join(BASE_DIR, "images")
HOTEL_IMAGES_DIR = os.path.join(BASE_DIR, "hotel_image")

# Create directories
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(HOTEL_IMAGES_DIR, exist_ok=True)

# ============================================================
# DEFAULT OWNER CONFIG
# ============================================================
# DEFAULT_OWNER_CONFIG = {
#     "username": "Minte",
#     "password": "Minte1234"
# }

# ============================================================
# JSON FUNCTIONS
# ============================================================
# def load_owner_config():
#     try:
#         with open(OWNER_CONFIG_PATH, "r",encoding="utf-8") as f:
#             return json.load(f)

#     except (FileNotFoundError, json.JSONDecodeError):
#         with open(OWNER_CONFIG_PATH, "w", encoding="utf-8") as f:
#             json.dump(DEFAULT_OWNER_CONFIG, f, indent=2)
#         return DEFAULT_OWNER_CONFIG

# def save_owner_config(config):
#     with open(OWNER_CONFIG_PATH, "w", encoding="utf-8") as f:
#         json.dump(config, f, indent=2, ensure_ascii=False)

def load_json():
    try:
        with open(CUSTOMER_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_json(data):
    with open(CUSTOMER_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ============================================================
# SIMPLE AUTH STATE
# ============================================================
#logged_in = False
current_language = "first_language"

# ============================================================
# PYDANTIC MODELS
# ============================================================
# class LoginRequest(BaseModel):
#     username: str
#     password: str

# class ChangePasswordRequest(BaseModel):
#     old_password: str
#     new_username: str
#     new_password: str

class SelectLanguageRequest(BaseModel):
    lang_key: str

class ToggleVisibilityRequest(BaseModel):
    product_type: str
    product_key: str

class UpdateProductRequest(BaseModel):
    product_type: str
    product_key: str
    field: str
    value: str

# ============================================================
# AUTH HELPER
# ============================================================
# def require_login():
#     global logged_in
#     if not logged_in:
#         raise HTTPException(
#             status_code=401,
#             detail="Not logged in"
#         )


# ============================================================
# IMAGES
# ============================================================
app.mount(
    "/images",
    StaticFiles(directory=IMAGES_DIR),
    name="images"
)
app.mount(
    "/hotel_image",
    StaticFiles(directory=HOTEL_IMAGES_DIR),
    name="hotel_image"
)

# ============================================================
# AUTHENTICATION
# ============================================================
# @app.post("/api/owner/login")
# def owner_login(data: LoginRequest):
#     global logged_in
#     config = load_owner_config()
#     if (data.username == config.get("username") and data.password == config.get("password")):
#         logged_in = True
#         return {
#             "success": True,
#             "message": "Login successful"
#         }
#     return {
#         "success": False,
#         "message": "Invalid credentials"
#     }

# ============================================================
# @app.post("/api/owner/logout")
# def owner_logout():
#     global logged_in
#     logged_in = False
#     return {
#         "success": True,
#         "message": "Logged out successfully"
#     }

# # ============================================================
# @app.get("/api/owner/check_auth")
# def check_auth():
#     return {
#         "logged_in": logged_in
#     }

# # ============================================================
# @app.post("/api/owner/change_password")
# def change_password(data: ChangePasswordRequest):
#     global logged_in
#     require_login()
#     config = load_owner_config()
#     if data.old_password != config.get("password"):
#         raise HTTPException(
#             status_code=401,
#             detail="Old password is incorrect"
#         )
#     config["username"] = data.new_username
#     config["password"] = data.new_password
#     save_owner_config(config)
#     logged_in = False
#     return {
#         "success": True,
#         "message": "Credentials updated. Please login again."
#     }


# ============================================================
# LANGUAGE
# ============================================================
@app.get("/api/owner/languages")
def get_languages():
    return {
        "buttons": [
            {
                "key": "first_language",
                "name": "English"
            },
            {
                "key": "second_language",
                "name": "አማርኛ"
            }
        ]
    }

# ============================================================
@app.post("/api/owner/select_language")
def select_language(data: SelectLanguageRequest):
    global current_language
    allowed_languages = [
        "first_language",
        "second_language"
    ]
    if data.lang_key not in allowed_languages:
        raise HTTPException(
            status_code=400,
            detail="Invalid language"
        )
    current_language = data.lang_key
    return {
        "success": True,
        "lang": current_language
    }
    
# ============================================================
# PRODUCT HELPERS
# ============================================================
def get_product_dictionary(customer_data, lang_key, product_type):
    language_menu = customer_data["language_menu"][lang_key]
    if product_type == "food":
        return language_menu["food"]["product"]
    if product_type == "drink":
        return language_menu["drink"]["product"]
    if product_type == "room":
        return language_menu["room"]["room_list"]
    if product_type == "vip_room":
        return language_menu["vip_room"]["room_list"]
    raise HTTPException(
        status_code=400,
        detail=f"Unknown product type: {product_type}"
    )


def find_product(product_dictionary, product_key):
    # Exact match
    if product_key in product_dictionary:
        return product_dictionary[product_key]
    # Cleaned match
    clean_product_key = product_key.strip()
    for key, value in product_dictionary.items():
        if key.strip() == clean_product_key:
            return value
    # Partial match
    for key, value in product_dictionary.items():
        if product_key in key:
            return value
    raise HTTPException(
        status_code=404,
        detail=f"Product '{product_key}' not found"
    )


# ============================================================
# FOOD ITEMS
# ============================================================
@app.get("/api/owner/food_items")
def get_food_items(lang: str = "first_language"):
    customer_data = load_json()
    if not customer_data:
        return {
            "items": []
        }
    try:
        food_items = (customer_data["language_menu"][lang]["food"]["product"])
        items = []
        for key, item in food_items.items():
            if (key != "types" and isinstance(item, dict)):
                items.append({
                    "key": key,
                    "name": item.get("name", key),
                    "description": item.get("description", ""),
                    "price": item.get("price", 0),
                    "currency": item.get("currenc", "$"),
                    "image": item.get("image", ""),
                    "price_label": item.get("lang_price", "Price"),
                    "visible": item.get("visible", True)
                })
        return {
            "items": items
            }

    except Exception as e:
        return {
            "items": [],
            "error": str(e)
        }

# ============================================================
# DRINK ITEMS
# ============================================================
@app.get("/api/owner/drink_items")
def get_drink_items(lang: str = "first_language"):
    customer_data = load_json()
    if not customer_data:
        return {
            "items": []
        }
    try:
        drink_items = (customer_data["language_menu"][lang]["drink"]["product"])
        items = []
        for key, item in drink_items.items():
            if (key != "types" and isinstance(item, dict)):
                items.append({
                    "key": key,
                    "name": item.get("name", key),
                    "description": item.get("description", ""),
                    "price": item.get("price", 0),
                    "currency": item.get( "currenc", "$"),
                    "image": item.get("image", ""),
                    "price_label": item.get("lang_price", "Price"),
                    "visible": item.get("visible", True)
                })
        return {
            "items": items
        }
    except Exception as e:
        return {
            "items": [],
            "error": str(e)
        }

# ============================================================
# ROOM ITEMS
# ============================================================
@app.get("/api/owner/room_items")
def get_room_items(lang: str = "first_language"):
    customer_data = load_json()
    if not customer_data:
        return {
            "items": []
        }
    try:
        room_items = (customer_data["language_menu"][lang]["room"]["room_list"])
        items = []
        for key, item in room_items.items():
            if (key != "types" and isinstance(item, dict)):
                clean_key = key.strip()
                items.append({
                    "key": clean_key,
                    "name": item.get("name", clean_key),
                    "description": item.get("description", ""),
                    "price": item.get("price", 0),
                    "currency": item.get("currenc", "$"),
                    "image": item.get("image", ""),
                    "price_label": item.get("lang_price", "Price"),
                    "visible": item.get("visible", True)
                })
        return {
            "items": items
        }
    except Exception as e:
        return {
            "items": [],
            "error": str(e)
        }


# ============================================================
# VIP ROOM ITEMS
# ============================================================
@app.get("/api/owner/vip_room_items")
def get_vip_room_items(lang: str = "first_language"):
    customer_data = load_json()
    if not customer_data:
        return {
            "items": []
        }
    try:
        vip_items = (customer_data["language_menu"][lang]["vip_room"]["room_list"])
        items = []
        for key, item in vip_items.items():
            if (key != "types" and isinstance(item, dict)):
                clean_key = key.strip()
                items.append({
                    "key": clean_key,
                    "name": item.get("name", clean_key),
                    "description": item.get("description", ""),
                    "price": item.get("price", 0),
                    "currency": item.get("currenc", "$"),
                    "image": item.get("image", ""),
                    "price_label": item.get("lang_price", "Price"),
                    "visible": item.get("visible", True)
                })
        return {
            "items": items
        }
    except Exception as e:
        return {
            "items": [],
            "error": str(e)
        }

# ============================================================
# TOGGLE VISIBILITY
# ===========================================================
@app.post("/api/owner/toggle_visibility")
def toggle_visibility(data: ToggleVisibilityRequest):
    #require_login()
    customer_data = load_json()
    if not customer_data:
        raise HTTPException(status_code=500, detail="JSON file not found")
    global current_language
    try:
        product_dictionary = get_product_dictionary(customer_data, current_language, data.product_type)
        target = find_product(product_dictionary, data.product_key)
        current_status = target.get("visible", True)
        target["visible"] = not current_status
        save_json(customer_data)
        status_text = ("enabled" if target["visible"] else "disabled")
        return {
            "success": True,
            "message": (f"Product {status_text} successfully"),
            "visible": target["visible"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# UPDATE PRODUCT
# ============================================================
@app.post("/api/owner/update_product")
def update_product(data: UpdateProductRequest):
    #require_login()
    allowed_fields = ["name", "description", "price"]
    if data.field not in allowed_fields:
        raise HTTPException(status_code=400, detail="Invalid field")
    customer_data = load_json()
    if not customer_data:
        raise HTTPException(status_code=500, detail="JSON file not found")
    global current_language
    try:
        product_dictionary = get_product_dictionary(customer_data, current_language, data.product_type)
        target = find_product(product_dictionary, data.product_key)
        if data.field == "name":
            target["name"] = data.value
        elif data.field == "description":
            target["description"] = data.value
        elif data.field == "price":
            target["price"] = float(data.value)
        save_json(customer_data)
        return {
            "success": True,
            "message": (f"{data.field} updated successfully")
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Price must be a number")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# UPLOAD IMAGE
# ============================================================
@app.post("/api/owner/upload_image")
async def upload_image(
    image: UploadFile = File(...),
    product_type: str = Form(...),
    product_key: str = Form(...)
):
    #require_login()
    global current_language
    allowed_types = ["food", "drink", "room", "vip_room"]
    if product_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid product type")
    if not image.filename:
        raise HTTPException(status_code=400, detail="No image selected")

    # --------------------------------------------------------
    # Determine directory
    # --------------------------------------------------------
    if product_type in ["room", "vip_room"]:
        img_dir = HOTEL_IMAGES_DIR
        web_path = "hotel_image"
    else:
        img_dir = IMAGES_DIR
        web_path = "images"
    os.makedirs(img_dir, exist_ok=True)

    # --------------------------------------------------------
    # Filename
    # --------------------------------------------------------
    timestamp = int(time.time())
    safe_key = product_key.replace(" ", "_")
    filename = (
        f"{product_type}_"
        f"{safe_key}_"
        f"{current_language}"
    )

    image_path = os.path.join(img_dir, filename)

    # --------------------------------------------------------
    # Save image
    # --------------------------------------------------------
    contents = await image.read()
    with open(image_path, "wb") as f:
        f.write(contents)
    web_image_path = (f"{web_path}/{filename}")

    # --------------------------------------------------------
    # Update JSON
    # --------------------------------------------------------
    customer_data = load_json()
    if not customer_data:
        raise HTTPException(status_code=500, detail="JSON file not found")
    try:
        product_dictionary = get_product_dictionary(customer_data, current_language, product_type)
        target = find_product(product_dictionary, product_key)
        target["image"] = web_image_path
        save_json(customer_data)
    except HTTPException:
        # Remove uploaded file if product doesn't exist
        if os.path.exists(image_path):
            os.remove(image_path)
        raise
    except Exception as e:
        if os.path.exists(image_path):
            os.remove(image_path)
        raise HTTPException(status_code=500, detail=str(e))

    # --------------------------------------------------------
    # Delete previous images
    # --------------------------------------------------------
    prefix = (
        f"{product_type}_"
        f"{safe_key}_"
        f"{current_language}_"
    )

    for old_file in os.listdir(img_dir):
        if (old_file.startswith(prefix) and old_file != filename):
            old_path = os.path.join(img_dir, old_file)
            try:
                os.remove(old_path)
            except OSError:
                pass
    return {
        "success": True,
        "message": "Image uploaded successfully",
        "image_path": web_image_path
    }

# ============================================================
# CONTACT INFO
# ============================================================
@app.get("/api/owner/contact_info")
def get_contact_info(lang: str = "first_language"):
    customer_data = load_json()
    contact_data = {
        "phone": "0951388278",
        "telegram": "https://t.me/Minte_contact",
        "email": "mintechatbot@gmail.com",
        "location": "Dilla, Ethiopia",
        "hours": "Mon-Sat: 8am-10pm | Sun: 12am-8pm"
    }
    if customer_data:
        try:
            contact_text = (customer_data["language_menu"][lang].get("contact", ""))
            if "0951388278" in contact_text:
                contact_data["phone"] = ("0951388278")
            if "t.me/Minte_contact" in contact_text:
                contact_data["telegram"] = ("https://t.me/Minte_contact")
            if "mintechatbot@gmail.com" in contact_text:
                contact_data["email"] = ("mintechatbot@gmail.com")
            if "Dilla" in contact_text:
                contact_data["location"] = ("Dilla, Ethiopia")
        except Exception:
            pass
    return contact_data

# ============================================================
# START
# ============================================================
if __name__ == "__main__":
    import uvicorn
    print("🚀 Minte Restaurant " "Owner Backed is LIVE...")
    print("📍 API: " "http://localhost:5001")
    print("📋 Updating: " + CUSTOMER_JSON_PATH)
    uvicorn.run(app, host="0.0.0.0", port=5001)


