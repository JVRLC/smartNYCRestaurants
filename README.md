# smartNYCRestaurants
Application Python pour localiser les restaurants à New York à partir de données PostgreSQL et MongoDB
---

```json
{   
    "address": -> geo
        {"building": "1007", "coord":{"type":"Point", "coordinates" : [-73.856077, 40.848447]}, "street": "Morris Park Ave", "zipcode": "10462"}, 
    "borough": "Bronx", -> main
    "cuisine": "Bakery",-> main
    "grades": -> feedback
        [{"date": {"$date": 1393804800000}, "grade": "A", "score": 2}, {"date": {"$date": 1378857600000}, "grade": "A", "score": 6}, {"date": {"$date": 1358985600000}, "grade": "A", "score": 10}, {"date": {"$date": 1322006400000}, "grade": "A", "score": 9}, {"date": {"$date": 1299715200000}, "grade": "B", "score": 14}], 
    "name": "Morris Park Bake Shop", -> main
    "restaurant_id": "30075445" -> main
}
```

