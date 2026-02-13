import json
from sklearn.metrics.pairwise import cosine_similarity


def recommend(product_id):

    products = json.load(open("products.json"))

    features = []

    for p in products:
        features.append([
            p["price"],
            p["ram"],
            p["storage"],
            p["rating"]
        ])

    similarity = cosine_similarity(features)

    index = next(i for i, p in enumerate(products)
                 if p["id"] == product_id)

    scores = list(enumerate(similarity[index]))
    scores = sorted(scores, key=lambda x: x[1], reverse=True)

    recommendations = [
        products[i[0]] for i in scores[1:4]
    ]

    return recommendations
