@app.get("/privacy")
def privacy_page():
    return render_template("privacy.html")

