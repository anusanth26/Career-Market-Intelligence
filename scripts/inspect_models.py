import joblib

def inspect_dict(model_path):
    print(f"\nInspecting {model_path}")
    model_data = joblib.load(model_path)
    print(f"Type: {type(model_data)}")
    if isinstance(model_data, dict):
        print("Keys:", list(model_data.keys()))
        for k, v in model_data.items():
            print(f"  - {k}: {type(v)}")
            if hasattr(v, 'feature_importances_'):
                print(f"    Has feature_importances_: {len(v.feature_importances_)}")
            elif hasattr(v, 'feature_names_in_'):
                print(f"    Has feature_names_in_: {len(v.feature_names_in_)}")
                
        # Check if 'model' key has steps
        if 'model' in model_data and hasattr(model_data['model'], 'steps'):
            print("    Model is a pipeline. Steps:")
            for name, step in model_data['model'].steps:
                print(f"      - {name}: {type(step)}")
            clf = model_data['model'].steps[-1][1]
            print(f"    Classifier type: {type(clf)}")
            if hasattr(clf, 'feature_importances_'):
                print(f"    Has feature_importances_: {len(clf.feature_importances_)}")
            elif hasattr(clf, 'coef_'):
                print(f"    Has coef_: {clf.coef_.shape}")
            if hasattr(model_data['model'][:-1], 'get_feature_names_out'):
                try:
                    features = model_data['model'][:-1].get_feature_names_out()
                    print(f"    Features in pipeline: {len(features)}")
                except Exception as e:
                    print(f"    Could not get feature names: {e}")

inspect_dict('models/salary_binary_model.joblib')
inspect_dict('models/salary_band_model.joblib')
