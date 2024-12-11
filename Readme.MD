# GuestMe (AirBnB-like Application)

**GuestMe** is a feature-rich AirBnB-like application that enables users to book homes and allows hosts to manage their properties, availability, and reservations efficiently. The application uses Flask, SQLAlchemy, and Flask-Login for its backend, and Google Maps API for interactive map integration.

## Features

### **For Users:**
- **Home Search and Map Integration:**  
  Users can browse available homes and view their exact locations on an interactive Google Map. Homes are color-coded based on their status:
  - **Green:** Available for booking
  - **Yellow:** Booked but pending approval
  - **Red:** Fully booked and approved

- **Detailed Property Information:**  
  Each property has a dedicated page displaying details such as:
  - Description
  - Price
  - Location
  - Availability on a calendar

- **Booking System:**  
  Users can book available dates directly from the property page. Only valid and open date ranges can be selected. 

- **Booking Management:**  
  Users can:
  - View all their past and current bookings
  - Cancel pending or approved bookings
  - View cancellation reasons (e.g., "Host deleted the property")

### **For Hosts:**
- **Add and Manage Properties:**  
  Hosts can add properties with details like:
  - Title, description, location, and price
  - Latitude and longitude (via interactive map)

- **Availability Management:**  
  Hosts can set and update the availability of their properties using a calendar system.

- **Reservation Management:**  
  Hosts can view incoming reservations and either approve or reject them. Approved reservations are locked, while rejected ones are canceled automatically.

- **Property Deletion:**  
  Hosts can delete properties. Deleting a property will:
  - Cancel all associated reservations
  - Notify users of the cancellation with the reason: "Host deleted the property."

### **Map Integration:**
- Homes are displayed on an interactive Google Map with markers colored based on their status.
- Users can click on markers to view property details.

## Pages

1. **Home Page:**  
   Displays a list of available properties and a map showing their locations.

2. **Property Detail Page:**  
   Detailed information about a specific property, with booking functionality.

3. **Manage Properties (for Hosts):**  
   Lists all properties added by the host, allowing them to manage availability, view reservations, and delete properties.

4. **Reservation Pages:**  
   - **For Users:** Displays their past and current reservations, with options to cancel pending or approved bookings.
   - **For Hosts:** Lists incoming reservations for their properties, with options to approve or reject.

5. **User Authentication:**  
   Includes registration, login, and logout functionalities, with distinct roles (`user` and `host`).

6. **Map View:**  
   A dedicated page to explore all available properties on a map.

## Installation and Setup

1. Clone this repository to your local machine.

2. Install the required dependencies using `pip`.

3. Create a `.env` file in the root directory with the following configuration:

    ```env
    SECRET_KEY=your_secret_key
    DATABASE_URL=sqlite:///guestme.db
    GOOGLE_MAPS_API_KEY=your_google_maps_api_key
    ```

4. Run the application using:

    ```bash
    python app.py
    ```

5. Open `http://127.0.0.1:5000` in your browser to access the application.

## Screenshots

### Main Screen:
<img src="https://github.com/can61cebi/GuestMe/blob/master/images/2.png" width="400">

### Property Detail Page:
<img src="https://github.com/can61cebi/GuestMe/blob/master/images/1.png" width="400">

---

If you need help choosing a license, you can start here: https://choosealicense.com/
