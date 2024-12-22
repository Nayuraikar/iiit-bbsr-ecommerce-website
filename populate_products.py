import os
import sqlite3

def add_products_from_images():
    images_folder = 'static/images'
    image_files = [f for f in os.listdir(images_folder) if f.endswith('.png')]  
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    for image_file in image_files:
        product_name = os.path.splitext(image_file)[0]  
        product_price = 19.99  
        
        c.execute("SELECT * FROM products WHERE name = ?", (product_name,))
        existing_product = c.fetchone()
        if not existing_product:
            c.execute("INSERT INTO products (name, price, image) VALUES (?, ?, ?)", (product_name, product_price, image_file))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_products_from_images()
