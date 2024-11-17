# Student ID: #012249526
# WGUPS Package Delivery Implementation
# This program implements a package delivery management system using hash tables
# and nearest neighbor algorithm for route optimization.

from datetime import datetime, timedelta
import csv

class Package:
    """Class representing a delivery package with all its attributes and status"""
    def __init__(self, package_id, address, city, state, zip_code, deadline, weight, notes=""):
        self.package_id = int(package_id)
        self.address = address.strip()
        self.city = city.strip()
        self.state = state.strip()
        self.zip_code = zip_code.strip()
        self.deadline = deadline.strip()
        self.weight = float(weight.strip() if weight.strip() else 0)
        self.notes = notes.strip()
        self.status = "at hub"
        self.delivery_time = None
        self.departure_time = None
        self.truck = None
        self.original_address = address.strip()  # Store original address

    def update_address(self, new_address, new_city, new_zip, update_time):
        """Updates package address after a specific time"""
        if self.departure_time and self.departure_time > update_time:
            self.address = new_address
            self.city = new_city
            self.zip_code = new_zip    

    def __str__(self):
        return f"Package {self.package_id}: {self.address}, {self.city}, {self.state} {self.zip_code}"

    def get_status(self, current_time=None):
        """Returns the status of the package at a given time"""
        if current_time is None:
            status = self.status
        else:
            # Update address for package 9 at 10:20 AM
            if self.package_id == 9:
                update_time = datetime.strptime("10:20 AM", "%I:%M %p")
                if current_time >= update_time:
                    self.update_address("410 S State St", "Salt Lake City", "84111", update_time)
                else:
                    # Reset to original address if before 10:20 AM
                    self.address = self.original_address
            
            if self.departure_time is None:
                status = "at hub"
            elif current_time < self.departure_time:
                status = "at hub"
            elif self.delivery_time is None or current_time < self.delivery_time:
                status = "en route"
            else:
                status = "delivered"
        
        return status

class HashTable:
    """Custom hash table implementation for package storage and retrieval"""
    def __init__(self, capacity=40):
        self.size = capacity
        self.table = [[] for _ in range(capacity)]

    def _hash(self, key):
        """Simple hash function using modulo"""
        return key % self.size

    def insert(self, key, item):
        """Insert or update an item in the hash table"""
        bucket = self._hash(key)
        for i, (k, v) in enumerate(self.table[bucket]):
            if k == key:
                self.table[bucket][i] = (key, item)
                return
        self.table[bucket].append((key, item))

    def lookup(self, key):
        """Look up an item by key"""
        bucket = self._hash(key)
        for k, v in self.table[bucket]:
            if k == key:
                return v
        return None

    def get_all(self):
        """Get all items in the hash table"""
        all_items = []
        for bucket in self.table:
            for _, item in bucket:
                all_items.append(item)
        return sorted(all_items, key=lambda x: x.package_id)

class Truck:
    """Class representing a delivery truck with its attributes and delivery capabilities"""
    def __init__(self, id, capacity=16, speed=18):
        self.id = id
        self.capacity = capacity
        self.speed = speed  # mph
        self.packages = []
        self.mileage = 0.0
        self.current_location = "HUB"  # Changed from hardcoded address to HUB
        self.time = datetime.strptime("8:00 AM", "%I:%M %p")

    def load_package(self, package):
        """Load a package onto the truck"""
        if len(self.packages) < self.capacity:
            self.packages.append(package)
            package.truck = self.id
            package.departure_time = self.time
            return True
        return False

    def deliver_package(self, package, distance):
        """Deliver a package and update truck status"""
        travel_time = distance / self.speed
        self.time += timedelta(hours=travel_time)
        self.mileage += float(distance)
        package.status = "delivered"
        package.delivery_time = self.time
        self.current_location = package.address
        self.packages.remove(package)



class DeliverySystem:
    """Main class handling the delivery system operations"""
    def __init__(self):
        self.packages = HashTable()
        self.distances = {}
        self.addresses = []
        self.address_mapping = {}
        self.trucks = [Truck(1), Truck(2), Truck(3)]



    def _clean_address(self, address):
        """Clean address format to match between package and distance data"""
        if not address:
            return ""
            
        # Handle HUB special cases
        if any(hub_indicator in address.upper() for hub_indicator in 
            ["WESTERN GOVERNORS UNIVERSITY", "4001 SOUTH 700 EAST", "HUB"]):
            return "HUB"
        
        # If address contains a newline, take the first line that contains a number
        if '\n' in address:
            lines = [line.strip() for line in address.split('\n') if line.strip()]
            # Find first line containing a number
            for line in lines:
                if any(char.isdigit() for char in line):
                    address = line
                    break
        
        # Remove any zip code in parentheses
        address = address.split('(')[0].strip()
        
        # Remove suite/apt numbers
        if '#' in address:
            address = address.split('#')[0].strip()
        
        # Special case for Valley Central Station
        if "Valley Central" in address:
            address = address.replace("Station", "Sta")
        
        # Standardize street abbreviations
        address = (address.replace(' St ', ' Street ')
                        .replace(' Ave ', ' Avenue ')
                        .replace(' Blvd ', ' Boulevard ')
                        .replace(' Rd ', ' Road ')
                        .replace(' S ', ' South ')
                        .replace(' N ', ' North ')
                        .replace(' E ', ' East ')
                        .replace(' W ', ' West '))
        
        # Convert multiple spaces to single space and strip
        address = ' '.join(address.split())
        
        # Special case handling for specific addresses
        special_cases = {
            "3575 West Valley Central Station bus Loop": "3575 West Valley Central Sta bus Loop",
            "3575 W Valley Central Station bus Loop": "3575 West Valley Central Sta bus Loop"
        }
        
        return special_cases.get(address, address)




    def load_package_data(self, filename):
        """Load package data from CSV file"""
        try:
            with open(filename, 'r', encoding='utf-8-sig') as file:
                reader = csv.reader(file)
                package_count = 0
                header_found = False
                
                for row in reader:
                    if not row or all(cell.strip() == "" for cell in row):
                        continue
                        
                    if not header_found and any("ID" in cell for cell in row):
                        header_found = True
                        continue
                    
                    if header_found and row[0].strip().isdigit():
                        while len(row) < 8:
                            row.append("")
                        
                        package = Package(
                            row[0],  # ID
                            row[1],  # Address
                            row[2],  # City
                            row[3],  # State
                            row[4],  # ZIP
                            row[5],  # Deadline
                            row[6],  # Weight
                            row[7]   # Notes
                        )
                        self.packages.insert(package.package_id, package)
                        package_count += 1

                print(f"Successfully loaded {package_count} packages.")
        except Exception as e:
            print(f"Error loading package data: {e}")
            raise

    def load_distance_data(self, filename):
        """Loads distance data from CSV file with specific address handling"""
        try:
            with open(filename, 'r', encoding='utf-8-sig') as file:
                reader = csv.reader(file)
                rows = list(reader)
                
                # Find the header row (contains WGU address)
                header_row_index = None
                for i, row in enumerate(rows):
                    if len(row) > 2 and "Western Governors University" in row[2]:
                        header_row_index = i
                        break
                
                if header_row_index is None:
                    raise ValueError("Could not find address header row")
                
                # Process header addresses
                header_row = rows[header_row_index]
                self.addresses = []
                
                # Add explicit hub mappings
                self.address_mapping["4001 South 700 East"] = "HUB"
                self.address_mapping["HUB"] = "HUB"
                self.address_mapping["Western Governors University"] = "HUB"
                
                for addr in header_row[2:]:  # Skip empty columns
                    if addr.strip():
                        clean_addr = self._clean_address(addr)
                        if clean_addr:
                            self.addresses.append(clean_addr)
                            # Map both original and clean versions
                            self.address_mapping[addr.strip()] = clean_addr
                            self.address_mapping[clean_addr] = clean_addr
                
                # Process distance data
                for row in rows[header_row_index + 1:]:
                    if not row or len(row) < 3:
                        continue
                    
                    # Clean the source address
                    from_addr = row[0].strip()
                    clean_from = self._clean_address(from_addr)
                    
                    if not clean_from:
                        continue
                        
                    self.distances[clean_from] = {}
                    
                    # Store distances
                    for i, distance in enumerate(row[2:]):
                        if i < len(self.addresses) and distance.strip():
                            try:
                                dist_value = float(distance.strip())
                                if dist_value >= 0:
                                    self.distances[clean_from][self.addresses[i]] = dist_value
                                    # Add reverse mapping for symmetrical distances
                                    if self.addresses[i] not in self.distances:
                                        self.distances[self.addresses[i]] = {}
                                    self.distances[self.addresses[i]][clean_from] = dist_value
                            except ValueError:
                                continue
                
                print(f"\nSuccessfully loaded distances for {len(self.addresses)} locations.")
                print(f"Number of source addresses: {len(self.distances)}")
                
        except Exception as e:
            print(f"Error loading distance data: {e}")
            raise
   
    def get_distance(self, addr1, addr2):
        """Get the distance between two addresses with improved matching"""
        try:
            # Clean both addresses
            addr1_clean = self._clean_address(addr1)
            addr2_clean = self._clean_address(addr2)
            
            # Debug logging
            print(f"\nDebug - Distance lookup:")
            print(f"Original addr1: '{addr1}'")
            print(f"Cleaned addr1: '{addr1_clean}'")
            print(f"Original addr2: '{addr2}'")
            print(f"Cleaned addr2: '{addr2_clean}'")
            print(f"Available addresses in distance table: {list(self.distances.keys())[:3]}...")  # Show first 3
            
            # Direct lookup
            if addr1_clean in self.distances and addr2_clean in self.distances[addr1_clean]:
                print(f"Found direct distance: {self.distances[addr1_clean][addr2_clean]}")
                return float(self.distances[addr1_clean][addr2_clean])
            elif addr2_clean in self.distances and addr1_clean in self.distances[addr2_clean]:
                print(f"Found reverse distance: {self.distances[addr2_clean][addr1_clean]}")
                return float(self.distances[addr2_clean][addr1_clean])
            
            # Try looking up using mapped addresses
            addr1_mapped = self.address_mapping.get(addr1_clean, addr1_clean)
            addr2_mapped = self.address_mapping.get(addr2_clean, addr2_clean)
            
            print(f"Mapped addr1: '{addr1_mapped}'")
            print(f"Mapped addr2: '{addr2_mapped}'")
            
            if addr1_mapped in self.distances and addr2_mapped in self.distances[addr1_mapped]:
                print(f"Found mapped distance: {self.distances[addr1_mapped][addr2_mapped]}")
                return float(self.distances[addr1_mapped][addr2_mapped])
            elif addr2_mapped in self.distances and addr1_mapped in self.distances[addr2_mapped]:
                print(f"Found reverse mapped distance: {self.distances[addr2_mapped][addr1_mapped]}")
                return float(self.distances[addr2_mapped][addr1_mapped])
            
            # For debugging
            if addr1 != "4001 South 700 East":  # Reduce noise from hub address
                print(f"Failed to find distance between '{addr1}' and '{addr2}'")
                print(f"Available mappings: {list(self.address_mapping.items())[:3]}...")  # Show first 3
            
            return float('inf')
                
        except Exception as e:
            print(f"Error getting distance between {addr1} and {addr2}: {e}")
            return float('inf')





    def find_nearest(self, current_location, available_packages):
        """Find the nearest package from the current location"""
        if not available_packages:
            return None
        return min(available_packages, 
                  key=lambda p: self.get_distance(current_location, p.address))

    def optimize_delivery(self):
        """Optimize package delivery routes using the nearest neighbor algorithm"""
        print("Starting package sorting...")
        packages = self.packages.get_all()
        priority_packages = []
        delayed_packages = []
        truck2_packages = []
        regular_packages = []

        # Sort packages based on constraints
        for package in packages:
            if "Can only be on truck 2" in package.notes:
                truck2_packages.append(package)
            elif "Delayed" in package.notes:
                delayed_packages.append(package)
            elif package.deadline != "EOD":
                priority_packages.append(package)
            else:
                regular_packages.append(package)

        # Handle special delivery requirements
        linked_packages = {
            13: [15, 19],
            15: [13, 19],
            19: [13, 15]
        }

        # Ensure linked packages stay together
        for base_id, linked_ids in linked_packages.items():
            base_package = self.packages.lookup(base_id)
            if base_package in priority_packages:
                for linked_id in linked_ids:
                    linked_package = self.packages.lookup(linked_id)
                    if linked_package not in priority_packages:
                        priority_packages.append(linked_package)
                        if linked_package in regular_packages:
                            regular_packages.remove(linked_package)

        print("Distributing packages to trucks...")
        # Distribute packages among trucks
        truck1_packages = [p for p in priority_packages if p not in truck2_packages][:12]
        remaining_priority = [p for p in priority_packages if p not in truck1_packages]
        truck2_packages.extend(remaining_priority)
        
        # Fill remaining space on truck 2
        remaining_space = 16 - len(truck2_packages)
        truck2_packages.extend(regular_packages[:remaining_space])
        
        # Set delayed truck start time
        self.trucks[2].time = datetime.strptime("9:05 AM", "%I:%M %p")
        truck3_packages = delayed_packages + regular_packages[remaining_space:]

        # Route each truck
        self._route_truck(self.trucks[0], truck1_packages)
        self._route_truck(self.trucks[1], truck2_packages)
        self._route_truck(self.trucks[2], truck3_packages)

    def _route_truck(self, truck, packages):
        """Route a single truck using nearest neighbor algorithm"""
        print(f"Routing Truck {truck.id} with {len(packages)} packages...")
        try:
            # Load packages onto truck
            for package in packages:
                if truck.load_package(package):
                    print(f"Loaded package {package.package_id} onto truck {truck.id}")
                else:
                    print(f"Failed to load package {package.package_id} onto truck {truck.id}")

            # Deliver packages using nearest neighbor
            while truck.packages:
                next_delivery = self.find_nearest(truck.current_location, truck.packages)
                if next_delivery:
                    distance = self.get_distance(truck.current_location, next_delivery.address)
                    if distance != float('inf'):
                        truck.deliver_package(next_delivery, distance)
                    else:
                        print(f"Warning: Could not find distance for package {next_delivery.package_id}")
                        break
                else:
                    print(f"Warning: No next delivery found for truck {truck.id}")
                    break

            print(f"Truck {truck.id} routing complete.")
            
        except Exception as e:
            print(f"Error routing truck {truck.id}: {e}")
            raise

    def get_package_status(self, package_id, time=None):
        """Get the status of a package at a specific time"""
        package = self.packages.lookup(package_id)
        if not package:
            return None

        if time:
            query_time = datetime.strptime(time, "%I:%M %p")
            status = package.get_status(query_time)
        else:
            status = package.get_status()

        return {
            'id': package.package_id,
            'address': package.address,
            'deadline': package.deadline,
            'city': package.city,
            'zip': package.zip_code,
            'weight': package.weight,
            'status': status,
            'delivery_time': package.delivery_time,
            'truck': package.truck  # Added truck number
        }

    def get_total_mileage(self):
        """Calculate total mileage for all trucks"""
        return sum(truck.mileage for truck in self.trucks)
    
def main():
        """Main execution function for the WGUPS delivery system"""
        wgups = DeliverySystem()
        
        try:
            # Initialize the system
            print("WGUPS Package Delivery System")
            print("Initializing...")
            wgups.load_package_data('package_data.csv')
            wgups.load_distance_data('distance_data.csv')
            print("Data loaded successfully!")
            
            print("\nStarting route optimization...")
            wgups.optimize_delivery()
            print("Routes optimized successfully!")
            
            # Main program loop
            while True:
                print("\nWGUPS Package Tracking System")
                print("1. Check Package Status")
                print("2. Check All Packages Status")
                print("3. View Total Mileage")
                print("4. Exit")
                
                try:
                    choice = input("\nEnter your choice (1-4): ").strip()
                    
                    if choice == "1":
                        try:
                            package_id = int(input("Enter package ID (1-40): "))
                            if package_id < 1 or package_id > 40:
                                print("Invalid package ID. Please enter a number between 1 and 40.")
                                continue
                                
                            time_input = input("Enter time (HH:MM AM/PM) or press Enter for current status: ").strip()
                            
                            if time_input:
                                try:
                                    datetime.strptime(time_input, "%I:%M %p")
                                except ValueError:
                                    print("Invalid time format. Please use HH:MM AM/PM (e.g., 9:00 AM)")
                                    continue

                            status = wgups.get_package_status(package_id, time_input if time_input else None)
                            if status:
                                print("\nPackage Status Report")
                                print("-" * 50)
                                print(f"Package ID: {status['id']}")
                                print(f"Delivery Status: {status['status']}")
                                print(f"Address: {status['address']}")
                                print(f"City: {status['city']}")
                                print(f"Zip Code: {status['zip']}")
                                print(f"Delivery Deadline: {status['deadline']}")
                                print(f"Package Weight: {status['weight']} kg")
                                print(f"Assigned Truck: {status['truck']}")  # Added truck display
                                if status['delivery_time']:
                                    print(f"Delivery Time: {status['delivery_time'].strftime('%I:%M %p')}")
                                print("-" * 50)
                            else:
                                print(f"Package {package_id} not found.")
                        except ValueError:
                            print("Please enter a valid package ID number.")
                        
                    elif choice == "2":
                        time_input = input("Enter time (HH:MM AM/PM): ").strip()
                        try:
                            query_time = datetime.strptime(time_input, "%I:%M %p")
                            print("\nAll Packages Status Report")
                            print("-" * 100)
                            print(f"Status at {time_input}")
                            print("-" * 100)
                            print(f"{'ID':3} | {'Status':10} | {'Address':30} | {'Deadline':10} | {'Weight':6} | {'Delivery Time':12}")
                            print("-" * 100)
                            
                            for package in wgups.packages.get_all():
                                status = package.get_status(query_time)
                                delivery_time = package.delivery_time.strftime('%I:%M %p') if package.delivery_time else "Pending"
                                print(f"{package.package_id:3} | {status:10} | {package.address[:30]:30} | {package.deadline:10} | {package.weight:6} | {delivery_time:12}")
                            print("-" * 100)
                        except ValueError:
                            print("Invalid time format. Please use HH:MM AM/PM (e.g., 9:00 AM)")
                        
                    elif choice == "3":
                        print("\nMileage Report")
                        print("-" * 40)
                        total_mileage = wgups.get_total_mileage()
                        print(f"Total mileage for all trucks: {total_mileage:.1f} miles")
                        for truck in wgups.trucks:
                            print(f"Truck {truck.id}: {truck.mileage:.1f} miles")
                        print("-" * 40)
                        
                    elif choice == "4":
                        print("\nThank you for using WGUPS Package Tracking System!")
                        break
                        
                    else:
                        print("Invalid choice. Please enter a number between 1 and 4.")
                        
                except Exception as e:
                    print(f"An error occurred: {e}")
                    print("Please try again.")
                    
        except Exception as e:
            print(f"System initialization error: {e}")
            import traceback
            traceback.print_exc()
            return

if __name__ == "__main__":
    main()
        