from fastapi import FastAPI
from pydantic import BaseModel, conlist
from typing import List, Optional
import pandas as pd
import os
from model import recommend, output_recommended_recipes

# Load dataset (ensure correct file path)
DATASET_PATH = os.getenv("DATASET_PATH", "../Data/dataset.csv")
dataset = pd.read_csv(DATASET_PATH, compression='gzip')

app = FastAPI()

# Disease-to-ingredient mapping
disease_restrictions = {
    "diabetes": ["sugar", "honey", "white bread"],
    "hypertension": ["salt", "processed meats", "canned foods"],
    "heart disease": ["red meat", "butter", "fried foods"],
    "kidney disease": ["high sodium foods", "processed cheese", "canned soups"]
}

# Request parameter model
class Params(BaseModel):
    n_neighbors: int = 5
    return_distance: bool = False

class PredictionIn(BaseModel):
    nutrition_input: conlist(float, min_items=9, max_items=9)
    ingredients: List[str] = []
    diseases: List[str] = []  # New field for diseases
    params: Optional[Params] = None  # Ensure default is handled

# Recipe output model
class Recipe(BaseModel):
    Name: str
    CookTime: str
    PrepTime: str
    TotalTime: str
    RecipeIngredientParts: List[str]
    Calories: float
    FatContent: float
    SaturatedFatContent: float
    CholesterolContent: float
    SodiumContent: float
    CarbohydrateContent: float
    FiberContent: float
    SugarContent: float
    ProteinContent: float
    RecipeInstructions: List[str]

class PredictionOut(BaseModel):
    output: List[Recipe] = []  # Default to empty list

@app.get("/")
def home():
    return {"health_check": "OK"}

@app.post("/predict/", response_model=PredictionOut)
def update_item(prediction_input: PredictionIn):
    # Exclude ingredients based on diseases
    restricted_ingredients = set()
    for disease in prediction_input.diseases:
        if disease in disease_restrictions:
            restricted_ingredients.update(map(str.lower, disease_restrictions[disease]))
    
    # Remove restricted ingredients from user input (case-insensitive match)
    filtered_ingredients = [ing for ing in prediction_input.ingredients if ing.lower() not in restricted_ingredients]
    
    # Ensure params is not None
    params_dict = prediction_input.params.dict() if prediction_input.params else {"n_neighbors": 5, "return_distance": False}

    # Get recommendations
    recommendation_dataframe = recommend(dataset, prediction_input.nutrition_input, filtered_ingredients, params_dict)
    output = output_recommended_recipes(recommendation_dataframe)
    
    return {"output": output if output else []}
