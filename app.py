from flask import Flask, jsonify, request, send_from_directory
from flask_restful import Api, Resource
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import psycopg2
import psycopg2.extras
import joblib
import pandas as pd

app = Flask(__name__)
CORS(app)
api = Api(app)

DATABASE_URL = os.environ.get('DATABASE_URL')
db = psycopg2.connect(DATABASE_URL)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

model = joblib.load('adoption_model.pkl')
model_columns = joblib.load('model_columns.pkl')


class CatList(Resource):
    def get(self):
        cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM cats")
        cats = cursor.fetchall()
        for cat in cats:
            cursor.execute("SELECT image_filename FROM cat_images WHERE cat_id=%s", (cat['id'],))
            images = cursor.fetchall()
            cat['images'] = [img['image_filename'] for img in images]
        cursor.close()
        return jsonify(cats)

class AddCat(Resource):
    def post(self):
        try:
            data = request.form.to_dict()
            files = request.files.getlist('pictures')
            filenames = []
            for file in files:
                if file:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    filenames.append(filename)
            # Prepare data for prediction
            cat_features = {
                'AgeDays': int(data['age_days']),
                'Gender': data['gender'],
                'Sterilized': data['sterilized'],
                'Primary Breed': data['primary_breed'],
                'Primary Color': data['primary_color'],
                'Intake Type': data['intake_type'],
                'Intake Condition': data['intake_condition']
            }
            cat_df = pd.DataFrame([cat_features])
            cat_encoded = pd.get_dummies(cat_df)
            cat_encoded = cat_encoded.reindex(columns=model_columns, fill_value=0)
            adoption_proba = model.predict_proba(cat_encoded)[0][1]
            adoption_chance = round(adoption_proba * 100, 2)
            # Insert into database
            cursor = db.cursor()
            cursor.execute(
                """
                INSERT INTO cats (name, age_days, gender, sterilized, primary_breed, primary_color, intake_type, intake_condition, status, adoption_chance)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    data['name'],
                    data['age_days'],
                    data['gender'],
                    data['sterilized'],
                    data['primary_breed'],
                    data['primary_color'],
                    data['intake_type'],
                    data['intake_condition'],
                    data['status'],
                    adoption_chance
                )
            )
            cat_id = cursor.lastrowid
            for filename in filenames:
                cursor.execute(
                    "INSERT INTO cat_images (cat_id, image_filename) VALUES (%s, %s)",
                    (cat_id, filename)
                )
            db.commit()
            cursor.close()
            return jsonify({"message": "Cat added successfully", "adoption_chance": adoption_chance}), 201
        except Exception as e:
            print(f"Error in AddCat: {e}")
            return jsonify({"error": str(e)}), 500

class DeleteCat(Resource):
    def delete(self, cat_id):
        cursor = db.cursor()
        # Delete images from server
        cursor.execute("SELECT image_filename FROM cat_images WHERE cat_id=%s", (cat_id,))
        images = cursor.fetchall()
        for img in images:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], img[0])
            if os.path.exists(image_path):
                os.remove(image_path)
        cursor.execute("DELETE FROM cats WHERE id=%s", (cat_id,))
        db.commit()
        cursor.close()
        return jsonify({"message": "Cat deleted successfully"}), 200

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

api.add_resource(CatList, '/api/cats')
api.add_resource(AddCat, '/api/cats/add')
api.add_resource(DeleteCat, '/api/cats/<int:cat_id>/delete')

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
