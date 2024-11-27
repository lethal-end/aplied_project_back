import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib

data = pd.read_csv('aac_intakes_outcomes.csv')

data = data[data['animal_type'] == 'Cat']

adopted_outcomes = ['Adoption', 'Return to Owner']
data['Adopted'] = data['outcome_type'].apply(lambda x: 1 if x in adopted_outcomes else 0)

data = data.dropna(subset=['Adopted', 'age_upon_outcome_(days)', 'breed', 'color', 'sex_upon_outcome'])

# using 'age_upon_outcome_(days)' as 'AgeDays'
data['AgeDays'] = data['age_upon_outcome_(days)']

# extracting gender and sterilization status
def extract_gender(sex):
    if 'Male' in sex:
        return 'Male'
    elif 'Female' in sex:
        return 'Female'
    else:
        return 'Unknown'

def extract_sterilization(sex):
    if 'Spayed' in sex or 'Neutered' in sex:
        return 'Yes'
    elif 'Intact' in sex:
        return 'No'
    else:
        return 'Unknown'

data['Gender'] = data['sex_upon_outcome'].apply(extract_gender)
data['Sterilized'] = data['sex_upon_outcome'].apply(extract_sterilization)

# simplifying breeds
def simplify_breed(breed):
    if '/' in breed:
        return breed.split('/')[0]
    elif 'Mix' in breed:
        return breed.replace(' Mix', '')
    else:
        return breed

data['Primary Breed'] = data['breed'].apply(simplify_breed)

# simplifying colors
def simplify_color(color):
    if '/' in color:
        return color.split('/')[0]
    else:
        return color

data['Primary Color'] = data['color'].apply(simplify_color)

# selecting features
features = ['AgeDays', 'Gender', 'Sterilized', 'Primary Breed', 'Primary Color', 'intake_type', 'intake_condition']
data_model = data[features + ['Adopted']]

# dropping rows with missing feature values
data_model = data_model.dropna()

# encoding categorical variables
categorical_features = ['Gender', 'Sterilized', 'Primary Breed', 'Primary Color', 'intake_type', 'intake_condition']
data_encoded = pd.get_dummies(data_model, columns=categorical_features)

# preparing feature matrix and target vector
X = data_encoded.drop('Adopted', axis=1)
y = data_encoded['Adopted']

# splitting data 
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# training the model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# evaluation
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))

# trained model and feature columns
joblib.dump(model, 'adoption_model.pkl')
joblib.dump(list(X.columns), 'model_columns.pkl')
