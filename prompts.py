def get_restaurants_prompt(city):
    """
    Generate a prompt for finding gluten-free restaurants in a specific city.
    
    Args:
        city (str): The city name to search for restaurants
        
    Returns:
        str: Formatted prompt string
    """
    return f"""
    Find up to 20 dedicated gluten-free restaurants and cafes in {city}.
    Return only the restaurant names as a simple list, even if fewer than 20 are available.

    If no dedicated gluten-free restaurants are available, then find up to 20 restaurants or cafes with a gluten-free menu option instead.
    Again, return only the restaurant names as a simple list, even if fewer than 20 are available.

    Do not include any other information or formatting.
    """


'''
    Find up to 10 gluten-free restaurants and cafes in {city}.
    Return only the restaurant names as a simple list, even if fewer than 10 are available.
    Do not include any other information or formatting.
'''