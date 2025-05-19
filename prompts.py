def get_restaurants_prompt(city, type_="restaurants"):
    """
    Generate a prompt for finding gluten-free restaurants or cafes in a specific city.
    
    Args:
        city (str): The city name to search for establishments
        type_ (str): Type of establishment to search for ('restaurants' or 'cafes')
        
    Returns:
        str: Formatted prompt string
    """
    if type_ == "cafes":
        return f"""
        Find up to 20 gluten-free cafes and bakeries in {city}.
        Return only the cafe names as a simple list with numbers, even if fewer than 20 are available.

        If no gluten-free cafes are available, then find up to 20 cafes with a gluten-free menu option instead.
        Again, return only the cafe names as a simple list with numbers, even if fewer than 20 are available.

        Do not include any other information or formatting.
        """
    else:
        return f"""
        Find up to 20  gluten-free restaurants in {city}.
        Return only the restaurant names as a simple list with numbers, even if fewer than 20 are available.

        If no gluten-free restaurants are available, then find up to 20 restaurants with a gluten-free menu option instead.
        Again, return only the restaurant names as a simple list with numbers, even if fewer than 20 are available.

        Do not include any other information or formatting.
        """

