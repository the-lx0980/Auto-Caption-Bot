from tmdbv3api import TMDb, TV, Season
import datetime

def get_season_release_year_robust(series_name, season_number):
    """
    Finds the accurate release year for a specific season of a TV series.
    
    Args:
        series_name (str): The name of the series (e.g., "The Crown").
        season_number (int): The season number (e.g., 4).
        api_key (str): Your TMDb API key.
        
    Returns:
        str: The release year or a descriptive error message.
    """
    tmdb = TMDb()
    tmdb.api_key = api_key
    tmdb.language = "en"
    
    tv = TV()
    season = Season()

    try:
        # 1️⃣ Search for the TV series
        search_results = tv.search(series_name)
        if not search_results:
            return f"❌ Series '{series_name}' not found on TMDb."

        # Use first match (most relevant)
        series = search_results[0]
        series_id = series.id

        # 2️⃣ Fetch season details
        season_details = season.details(series_id, season_number)
        air_date = getattr(season_details, "air_date", None)

        # 3️⃣ Extract and format year
        if air_date:
            try:
                release_date = datetime.datetime.strptime(air_date, "%Y-%m-%d")
                return str(release_date.year)
            except ValueError:
                return f"⚠️ Invalid air_date format for season {season_number} of '{series_name}'."
        else:
            return f"ℹ️ No air date found for season {season_number} of '{series_name}'."

    except Exception as e:
        return f"⚠️ Error fetching details for '{series_name}' (Season {season_number}): {e}"


# Example usage
if __name__ == "__main__":
    api_key = "YOUR_API_KEY"  # Replace with your TMDb API key
    
    # Valid series
    print(get_season_release_year_robust("The Crown", 4, api_key))
    
    # Invalid series
    print(get_season_release_year_robust("NonExistent Series 123", 1, api_key))
