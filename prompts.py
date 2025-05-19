def get_restaurants_prompt(city):
    """
    Generate a prompt for finding gluten-free restaurants in a specific city.
    
    Args:
        city (str): The city name to search for restaurants
        
    Returns:
        str: Formatted prompt string
    """
    return f"""
    Find me up to 10 dedicated gluten-free restaurants and cafés within 5 km of central {city} (100% gluten-free kitchens with no risk of cross-contamination). Also include restaurants that offer a clearly labeled gluten-free menu section.

    For each entry, return:
    - Restaurant Name
    - Address (including postal code)
    - Contact Details (phone with +358 country code, email, website URL)
    - Type of Cuisine
    - Opening Hours
    - Average User Rating (e.g. Google or Yelp)
    - Dedicated Gluten-Free or Separate Menu

    Present the results as a Markdown table with those columns. Sort the table by highest user rating first. Do not use bold formatting.
    """
