import numpy as np
import re
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer

def scaling(dataframe):
    scaler = StandardScaler()
    prep_data = scaler.fit_transform(dataframe.iloc[:, 6:15].to_numpy())
    return prep_data, scaler

def nn_predictor(prep_data):
    neigh = NearestNeighbors(metric='cosine', algorithm='brute')
    neigh.fit(prep_data)
    return neigh

def build_pipeline(neigh, scaler, params):
    transformer = FunctionTransformer(lambda X: neigh.kneighbors(scaler.transform(X), **params))
    pipeline = Pipeline([('std_scaler', scaler), ('NN', transformer)])
    return pipeline

def extract_data(dataframe, ingredients):
    extracted_data = dataframe.copy()
    extracted_data = extract_ingredient_filtered_data(extracted_data, ingredients)
    return extracted_data

def extract_ingredient_filtered_data(dataframe, ingredients):
    extracted_data = dataframe.copy()
    
    if ingredients:
        if isinstance(extracted_data['RecipeIngredientParts'].iloc[0], list):
            extracted_data = extracted_data[
                extracted_data['RecipeIngredientParts'].apply(lambda x: all(ing.lower() in map(str.lower, x) for ing in ingredients))
            ]
        else:
            regex_string = ''.join(map(lambda x: f'(?=.*{x})', ingredients))
            extracted_data = extracted_data[
                extracted_data['RecipeIngredientParts'].str.contains(regex_string, regex=True, flags=re.IGNORECASE, na=False)
            ]

    print(f"Filtered recipes count: {extracted_data.shape[0]}")  # Debugging
    
    if extracted_data.shape[0] < 5:
        print("Not enough recipes after filtering, relaxing the filtering criteria.")
        return dataframe  # Return full dataset as fallback
    
    return extracted_data

def apply_pipeline(pipeline, _input, extracted_data):
    try:
        _input = np.array(_input).reshape(1, -1)
        indices = pipeline.transform(_input)[0]
        print(f"Recommended recipe indices: {indices}")  # Debugging
        return extracted_data.iloc[indices]
    except Exception as e:
        print(f"Error in pipeline transformation: {e}")
        return None

def recommend(dataframe, _input, ingredients=[], params={'n_neighbors': 5, 'return_distance': False}):
    extracted_data = extract_data(dataframe, ingredients)
    
    if extracted_data.shape[0] < params['n_neighbors']:
        print("Not enough recipes after filtering, using general recommendations.")
        extracted_data = dataframe  # Fallback to the full dataset
    
    prep_data, scaler = scaling(extracted_data)
    neigh = nn_predictor(prep_data)
    pipeline = build_pipeline(neigh, scaler, params)
    return apply_pipeline(pipeline, _input, extracted_data)

def extract_quoted_strings(s):
    if isinstance(s, str):
        return re.findall(r'"([^"]*)"', s)
    return []

def output_recommended_recipes(dataframe):
    if dataframe is not None and not dataframe.empty:
        output = dataframe.to_dict("records")
        for recipe in output:
            recipe['RecipeIngredientParts'] = extract_quoted_strings(recipe.get('RecipeIngredientParts', ''))
            recipe['RecipeInstructions'] = extract_quoted_strings(recipe.get('RecipeInstructions', ''))
        return output
    else:
        print("No recommended recipes found.")  # Debugging
        return None
