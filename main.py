# Student ID: #000000000  # Replace with your actual student ID
# WGUPS Package Delivery Implementation
# This program implements a package delivery management system using hash tables
# and nearest neighbor algorithm for route optimization.

from datetime import datetime, timedelta
import csv

class Package:
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

    def __str__(self):
        return f"Package {self.package_id}: {self.address}, {self.city}, {self.state} {self.zip_code}"

    def get_status(self, current_time=None):
        if current_time is None:
            return self.status
            
        if self.departure_time is None:
            return "at hub"
        elif current_time < self.departure_time:
            return "at hub"
        elif self.delivery_time is None or current_time < self.delivery_time:
            return "en route"
        else:
            return "delivered"

class HashTable:
    def __init__(self, capacity=40):
        self.size = capacity
        self.table = [[] for _ in range(capacity)]

    def _hash(self, key):
        return key % self.size

    def insert(self, key, item):
        bucket = self._hash(key)
        for i, (k, v) in enumerate(self.table[bucket]):
            if k == key:
                self.table[bucket][i] = (key, item)
                return
        self.table[bucket].append((key, item))

    def lookup(self, key):
        bucket = self._hash(key)
        for k, v in self.table[bucket]:
            if k == key:
                return v
        return None

    def get_all(self):
        all_items = []
        for bucket in self.table:
            for _, item in bucket:
                all_items.append(item)
        return sorted(all_items, key=lambda x: x.package_id)

class Truck:
    def __init__(self, id, capacity=16, speed=18):
        self.id = id
        self.capacity = capacity
        self.speed = speed  # mph
        self.packages = []
        self.mileage = 0.0
        self.current_location = "HUB"
        self.time = datetime.strptime("8:00 AM", "%I:%M %p")

    def load_package(self, package):
        if len(self.packages) < self.capacity:
            self.packages.append(package)
            package.truck = self.id
            package.departure_time = self.time
            return True
        return False

    def deliver_package(self, package, distance):
        travel_time = distance / self.speed
        self.time += timedelta(hours=travel_time)
        self.mileage += float(distance)
        package.status = "delivered"
        package.delivery_time = self.time
        self.current_location = package.address
        self.packages.remove(package)

class DeliverySystem:
    def __init__(self):
        self.packages = HashTable()
        self.distances = {}
        self.addresses = []
        self.trucks = [Truck(1), Truck(2), Truck(3)]

    def load_package_data(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8-sig') as file:
                reader = csv.reader(file)
                package_data = []
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
                        package_data.append(row)

                if not package_data:
                    raise ValueError("No valid package data found in file")

                print(f"Successfully loaded {len(package_data)} packages.")
        except Exception as e:
            print(f"Error loading package data: {e}")
            raise

    def load_distance_data(self, filename):
        """Loads distance data from CSV file."""
        try:
            with open(filename, 'r', encoding='utf-8-sig') as file:
                reader = csv.reader(file)
                rows = list(reader)
                
                # Find the header row with addresses
                header_row_index = None
                for i, row in enumerate(rows):
                    if len(row) > 2 and "Western Governors University" in row[2]:  # Check third column
                        header_row_index = i
                        break
                
                if header_row_index is None:
                    raise ValueError("Could not find address header row")
                
                # Extract addresses from the header row
                header_row = rows[header_row_index]
                self.addresses = []
                for addr in header_row[2:]:  # Skip first two columns
                    if addr.strip():
                        # Extract first line of address for consistency
                        addr_first_line = addr.split('\n')[0].strip()
                        self.addresses.append(addr_first_line)
                
                # Process distance data starting from the row after header
                for row in rows[header_row_index + 1:]:
                    if not row or len(row) < 3:  # Skip empty rows
                        continue
                        
                    # Get source address (first line only)
                    from_addr = row[0].split('\n')[0].strip()
                    if not from_addr or from_addr == "HUB":
                        continue
                    
                    self.distances[from_addr] = {}
                    
                    # Process distances
                    for i, distance in enumerate(row[2:]):  # Skip first two columns
                        if i < len(self.addresses) and distance.strip():
                            try:
                                dist_value = float(distance.strip())
                                if dist_value >= 0:
                                    self.distances[from_addr][self.addresses[i]] = dist_value
                            except ValueError:
                                continue

                print(f"Successfully loaded distances for {len(self.addresses)} locations.")
                print(f"Number of source addresses: {len(self.distances)}")
                
        except Exception as e:
            print(f"Error loading distance data: {e}")
            raise





    def get_distance(self, addr1, addr2):
        try:
            # Clean addresses
            addr1_clean = ' '.join(addr1.split('\n')).strip()
            addr2_clean = ' '.join(addr2.split('\n')).strip()
            
            # Direct lookup
            if addr1_clean in self.distances and addr2_clean in self.distances[addr1_clean]:
                return float(self.distances[addr1_clean][addr2_clean])
            elif addr2_clean in self.distances and addr1_clean in self.distances[addr2_clean]:
                return float(self.distances[addr2_clean][addr1_clean])

            # Try partial matches
            for src_addr in self.distances:
                if addr1_clean in src_addr or src_addr in addr1_clean:
                    for dst_addr in self.distances[src_addr]:
                        if addr2_clean in dst_addr or dst_addr in addr2_clean:
                            return float(self.distances[src_addr][dst_addr])
                            
            # Try reverse lookup with partial matches
            for src_addr in self.distances:
                if addr2_clean in src_addr or src_addr in addr2_clean:
                    for dst_addr in self.distances[src_addr]:
                        if addr1_clean in dst_addr or dst_addr in addr1_clean:
                            return float(self.distances[src_addr][dst_addr])

            return float('inf')
        except Exception as e:
            print(f"Error getting distance between {addr1} and {addr2}: {e}")
            return float('inf')

    def find_nearest(self, current_location, available_packages):
        if not available_packages:
            return None
        return min(available_packages, key=lambda p: self.get_distance(current_location, p.address))

    def optimize_delivery(self):
        packages = self.packages.get_all()
        priority_packages = []
        delayed_packages = []
        truck2_packages = []
        regular_packages = []

        for package in packages:
            if "Can only be on truck 2" in package.notes:
                truck2_packages.append(package)
            elif "Delayed" in package.notes:
                delayed_packages.append(package)
            elif package.deadline != "EOD":
                priority_packages.append(package)
            else:
                regular_packages.append(package)

        truck1_packages = [p for p in priority_packages if p not in truck2_packages][:16]
        truck2_packages.extend([p for p in priority_packages if p not in truck1_packages])
        remaining_space = 16 - len(truck2_packages)
        truck2_packages.extend(regular_packages[:remaining_space])
        
        self.trucks[2].time = datetime.strptime("9:05 AM", "%I:%M %p")
        truck3_packages = delayed_packages + regular_packages[remaining_space:]

        self._route_truck(self.trucks[0], truck1_packages)
        self._route_truck(self.trucks[1], truck2_packages)
        self._route_truck(self.trucks[2], truck3_packages)

    def _route_truck(self, truck, packages):
        for package in packages:
            truck.load_package(package)

        while truck.packages:
            next_delivery = self.find_nearest(truck.current_location, truck.packages)
            if next_delivery:
                distance = self.get_distance(truck.current_location, next_delivery.address)
                if distance != float('inf'):
                    truck.deliver_package(next_delivery, distance)

    def get_package_status(self, package_id, time=None):
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
            'delivery_time': package.delivery_time
        }

    def get_total_mileage(self):
        return sum(truck.mileage for truck in self.trucks)

    def print_distance_debug(self):
        """Debug function to print loaded distance data"""
        print("\nDistance Data Debug Information:")
        print(f"Number of source addresses: {len(self.distances)}")
        print("\nSource addresses:")
        for addr in self.distances:
            print(f"- {addr}")
        print("\nDestination addresses:")
        for addr in self.addresses:
            print(f"- {addr}")
        print("\nSample distances:")
        for src in list(self.distances.keys())[:3]:
            print(f"\nFrom {src}:")
            for dst in list(self.distances[src].keys())[:3]:
                print(f"  To {dst}: {self.distances[src][dst]}")

def main():
    wgups = DeliverySystem()
    
    try:
        wgups.load_package_data('package_data.csv')
        wgups.load_distance_data('distance_data.csv')
        print("Data loaded successfully!")
        
        # Uncomment the next line to see debug information
        # wgups.print_distance_debug()
        
        wgups.optimize_delivery()
        print("Routes optimized successfully!")
        
    except Exception as e:
        print(f"Error during initialization: {e}")
        return

    while True:
        print("\nWGUPS Package Tracking System")
        print("1. Check Package Status")
        print("2. Check All Packages Status")
        print("3. View Total Mileage")
        print("4. Exit")
        
        choice = input("Enter your choice (1-4): ")
        
        if choice == "1":
            try:
                package_id = int(input("Enter package ID (1-40): "))
                time_input = input("Enter time (HH:MM AM/PM) or press Enter for current status: ")
                
                if time_input:
                    try:
                        datetime.strptime(time_input, "%I:%M %p")
                    except ValueError:
                        print("Invalid time format. Please use HH:MM AM/PM (e.g., 9:00 AM)")
                        continue

                status = wgups.get_package_status(package_id, time_input if time_input else None)
                if status:
                    print(f"\nPackage {status['id']} Status:")
                    print(f"Status: {status['status']}")
                    print(f"Address: {status['address']}")
                    print(f"Deadline: {status['deadline']}")
                    print(f"City: {status['city']}")
                    print(f"Zip: {status['zip']}")
                    print(f"Weight: {status['weight']} kg")
                    if status['delivery_time']:
                        print(f"Delivery Time: {status['delivery_time'].strftime('%I:%M %p')}")
                else:
                    print(f"Package {package_id} not found.")
            except ValueError:
                print("Please enter a valid package ID.")
                
        elif choice == "2":
            time_input = input("Enter time (HH:MM AM/PM): ")
            try:
                datetime.strptime(time_input, "%I:%M %p")
                print("\nPackage Status Report:")
                print("-" * 80)
                for package in wgups.packages.get_all():
                    status = package.get_status(datetime.strptime(time_input, "%I:%M %p"))
                    print(f"Package {package.package_id}: {status} - Deadline: {package.deadline}")
                print("-" * 80)
            except ValueError:
                print("Invalid time format. Please use HH:MM AM/PM (e.g., 9:00 AM)")
                
        elif choice == "3":
            total_mileage = wgups.get_total_mileage()
            print(f"\nTotal mileage for all trucks: {total_mileage:.1f} miles")
            for truck in wgups.trucks:
                print(f"Truck {truck.id}: {truck.mileage:.1f} miles")
                
        elif choice == "4":
            print("Thank you for using WGUPS Package Tracking System!")
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()