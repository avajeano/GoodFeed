# GoodFeed
https://goodfeed.onrender.com

## Overview

GoodFeed is a website that allows users to explore restaurants in New York City. Users can bookmark their favorite restaurants, review them, and manage a list of their bookmarked restaurants. Additionally, users can follow their friends to keep track of the reviews they post, making it easy to discover new dining spots recommended by their social circle.

### Features
- Login authentication
  - Bcrypt 
- Profile page
    - Renders all logged in users' reviews
      
      ![Screenshot 2024-07-30 at 10 26 48 PM](https://github.com/user-attachments/assets/7429a3c7-1dc2-4848-88a0-c196bfa81c81)

- Bookmarks
  - Bookmark/Unbookmark
      
      ![Screenshot 2024-07-30 at 10 32 13 PM](https://github.com/user-attachments/assets/73ab6e9a-07a2-4ae8-9afe-19ad5e89662c)

- Reviews
- Followers
    - Partial search capabilities
    - Follow/Unfollow funtionality
      
      ![Screenshot 2024-07-30 at 10 28 27 PM](https://github.com/user-attachments/assets/16057767-7f55-4634-b053-dbf18f0ccca3)

- Explore cuisines
  - Loops over all the different cuisines from the database

    ![Screenshot 2024-07-30 at 10 33 16 PM](https://github.com/user-attachments/assets/07398e1f-073b-416e-b703-53cd36c54b6e)

- Home page
    - Renders 20 random restaurants
 
## Entity Relationship Diagram

  ![Screenshot 2024-07-30 at 10 58 42 PM](https://github.com/user-attachments/assets/61e5cc00-5841-4399-b2cd-1423962229e3)


## API

https://data.cityofnewyork.us/Health/DOHMH-New-York-City-Restaurant-Inspection-Results/43nn-pn8j/about_data

## Tech Stack
- Python
- Flask
- PostgreSQL
- Jinja
- HTML
- Bootstrap

## Installation Instructions
1. Clone and download rep
2. Create virtual environment
3. ```flask run```
