def get_restaurants_prompt(city: str, type_: str = "restaurants") -> str:
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
        You are only allowed to search for **cafes and bakeries**, not restaurants.

        Find up to 20 **gluten-free cafes or bakeries** in {city}.
        Return **only the names** as a **simple numbered list**, even if fewer than 20 are available.

    **If no gluten-free cafes or bakeries are available**, then find up to 20 **cafes or bakeries** with a **gluten-free menu option** instead.
    Again, return **only the names** as a **simple numbered list**, even if fewer than 20 are available.

    **Do not include any restaurant names, labels, descriptions, or additional details.**
    **Return only the name of the cafe or bakery.**
    """
    else:
        return f"""
        You are only allowed to search for **restaurants**, not cafes or bakeries.

        Find up to 20 **gluten-free restaurants** in {city}.
        Return **only the names** as a **simple numbered list**, even if fewer than 20 are available.

        **If no gluten-free restaurants are available**, then find up to 20 **restaurants** with a **gluten-free menu option** instead.
        Again, return **only the names** as a **simple numbered list**, even if fewer than 20 are available.

        **Do not include any cafes, bakeries, labels, descriptions, or additional details.**
        **Return only the name of the restaurant.**
    """


