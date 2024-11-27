CREATE TABLE IF NOT EXISTS cats (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    age_days INT,
    gender VARCHAR(10),
    sterilized VARCHAR(10),
    primary_breed VARCHAR(50),
    primary_color VARCHAR(30),
    intake_type VARCHAR(30),
    intake_condition VARCHAR(30),
    status VARCHAR(20),
    adoption_chance REAL
);

CREATE TABLE IF NOT EXISTS cat_images (
    id SERIAL PRIMARY KEY,
    cat_id INT,
    image_filename VARCHAR(255),
    FOREIGN KEY (cat_id) REFERENCES cats(id) ON DELETE CASCADE
);
