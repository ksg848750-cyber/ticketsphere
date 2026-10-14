from fastapi import FastAPI, HTTPException

app = FastAPI(title="TicketSphere Event Service", version="2.0.0")

# Seed catalogue: the browser always loads these records through the Events API.
EVENTS = [
 {"id":"evt-101","name":"Hyderabad Tech Summit","category":"Technology","venue":"HITEX Exhibition Centre, Hyderabad","date":"2026-11-14","time":"10:00 AM","price":799,"emoji":"🚀","theme":"tech","description":"A full day of ideas, product demos, startup stories and conversations with builders shaping tomorrow."},
 {"id":"evt-102","name":"Indie Music Night","category":"Music","venue":"Heart Cup Coffee, Jubilee Hills","date":"2026-11-21","time":"7:00 PM","price":499,"emoji":"🎸","theme":"music","description":"An intimate live music evening with independent artists, acoustic sets and a crowd that loves discovering new sounds."},
 {"id":"evt-103","name":"Stand-up Comedy Live","category":"Comedy","venue":"Shilpakala Vedika, Hyderabad","date":"2026-12-05","time":"6:30 PM","price":599,"emoji":"🎤","theme":"comedy","description":"A live stand-up show packed with sharp observations, everyday chaos and brand-new material."},
 {"id":"evt-104","name":"Neon Dreams: DJ Night","category":"Nightlife","venue":"Prism Club, Hyderabad","date":"2026-11-28","time":"8:00 PM","price":999,"emoji":"🎧","theme":"nightlife","description":"A high-energy night of electronic music, immersive lights and a dance floor built for weekend plans."},
 {"id":"evt-105","name":"Canvas & Coffee Workshop","category":"Workshop","venue":"The Art House, Banjara Hills","date":"2026-11-18","time":"11:00 AM","price":699,"emoji":"🎨","theme":"art","description":"Learn a few painting techniques, experiment with colour and leave with your own original canvas. Materials included."},
 {"id":"evt-106","name":"Theatre: The Last Train","category":"Theatre","venue":"Ravindra Bharathi, Hyderabad","date":"2026-12-12","time":"6:00 PM","price":449,"emoji":"🎭","theme":"theatre","description":"A contemporary stage play about choices, second chances and the conversations we postpone for too long."},
 {"id":"evt-107","name":"Sunday Food Carnival","category":"Food","venue":"People's Plaza, Necklace Road","date":"2026-11-22","time":"12:00 PM","price":299,"emoji":"🍜","theme":"food","description":"Explore local favourites, street-food classics and new flavours from independent food stalls across the city."},
 {"id":"evt-108","name":"Sunrise 5K Community Run","category":"Sports","venue":"Gachibowli Stadium, Hyderabad","date":"2026-12-06","time":"6:00 AM","price":199,"emoji":"🏃","theme":"sports","description":"A friendly community run for first-timers and regular runners. Registration includes a bib and finishers medal."},
 {"id":"evt-109","name":"Acoustic Unplugged","category":"Music","venue":"Lamakaan, Banjara Hills","date":"2026-12-19","time":"7:30 PM","price":549,"emoji":"🎶","theme":"music","description":"A stripped-back concert with soulful vocals, acoustic arrangements and a relaxed outdoor atmosphere."},
 {"id":"evt-110","name":"AI Builders Meetup","category":"Technology","venue":"T-Hub, Hyderabad","date":"2027-01-09","time":"2:00 PM","price":399,"emoji":"🤖","theme":"tech","description":"Meet developers experimenting with AI, see practical demos and share what you are building."}
]

@app.get("/health")
def health(): return {"service":"events","status":"healthy"}

@app.get("/events")
def list_events(category: str | None = None, q: str | None = None):
    results = EVENTS
    if category and category.lower() not in ("all", "for you"):
        results = [e for e in results if e["category"].lower() == category.lower()]
    if q:
        term = q.strip().lower()
        results = [e for e in results if term in e["name"].lower() or term in e["category"].lower() or term in e["venue"].lower() or term in e["description"].lower()]
    return results

@app.get("/events/{event_id}")
def get_event(event_id: str):
    event = next((item for item in EVENTS if item["id"] == event_id), None)
    if event is None: raise HTTPException(status_code=404, detail="Event not found")
    return event
