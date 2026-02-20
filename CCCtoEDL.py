# CCC to EDL command line tool
# v1.1.0
# Last updated Feb 19th 2026
# Copyright (C) 2026  Moksh Chitkara
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import argparse
import os
import re
import glob
import fnmatch
import xml.etree.ElementTree as ET

verbose = False

def read_ccc_file(ccc_path):
    # Read the Color Correction Collection (CCC) file and extract the values needed
    tree = ET.parse(ccc_path)
    root = tree.getroot()

    # Extracting SOP values
    try:
        # Define a function to handle namespaces
        # Extract namespace
        if '{' in root.tag:
        	ns = {'cdl': root.tag.split('{')[1].split('}')[0]}
        else:
            ns = {'cdl': ''}

        # Find the necessary nodes
        slope = root.find('.//cdl:SOPNode/cdl:Slope', ns).text.split()
        offset = root.find('.//cdl:SOPNode/cdl:Offset', ns).text.split()
        power = root.find('.//cdl:SOPNode/cdl:Power', ns).text.split()
        saturation = root.find('.//cdl:SatNode/cdl:Saturation', ns).text.strip()
    except:
        print("[ERROR] Unable to parse:", ccc_path)
        slope = "1.000000 1.000000 1.000000".split()
        offset = "0.000000 0.000000 0.000000".split()
        power = "1.000000 1.000000 1.000000".split()
        saturation = "1.000000".strip() 
    
    return slope, offset, power, saturation

def read_edl_file(edl_path):
    # Read the initial EDL file and return its contents
    with open(edl_path, 'r') as file:
        content = file.readlines()
    return content

# Function to read the EDL file and extract event numbers and corresponding file names
def extract_event_mapping(edl_path):
    event_mapping = {}
    edl_file = read_edl_file(edl_path)
    for line in edl_file:
        # Look for lines that start with numbers (event lines)
        match = re.match(r'(\d{3})\s+(\S+)', line)
        if match:
            event_number = match.group(1)  # Get the event number (first group)
            file_name = match.group(2)      # Get the file name (second group)
            
            # Remove any extension (if present) for matching with CCC files
            base_name = os.path.splitext(file_name)[0]
            event_mapping[event_number] = base_name

    return event_mapping

# Searches for CCC files in the given directory and returns a dictionary with event numbers and their corresponding paths
def find_ccc_files(cccDir, edl_path, pattern):

    # Extract mapping from the EDL
    event_mapping = extract_event_mapping(edl_path)
    found_paths = {}

    # Loop through the specified directory and its subdirectories
    for root, dirs, files in os.walk(cccDir):
        for filename in fnmatch.filter(files, pattern):
            # Extract the base filename without the ".ccc" extension
            base_name = os.path.splitext(filename)[0]

            # Loop through the event mapping to find matches
            for event_number, event_base_name in event_mapping.items():
                if event_base_name == base_name:
                    found_paths[event_number] = os.path.join(root, filename)
                    if verbose:
                        print(event_number, found_paths[event_number])
                    break  # Stop after finding the first match

                elif loose and ((event_base_name.upper() in base_name.upper()) or (base_name.upper() in event_base_name.upper())):
                    found_paths[event_number] = os.path.join(root, filename)
                    if verbose:
                        print("[WARNING] Loose match:", event_number, found_paths[event_number])
                    break  # Stop after finding the first match

    if verbose:
        print("Found", len(found_paths), "CDL events for EDL")

    return found_paths

def write_output_edl(output_path, edl_content, ccc_dict):

    if verbose:
        print("Begining Write")

    # Prepare the output file contents
    output_content = []

    lastfind = False
    for line in edl_content:

        if line.startswith('TITLE:'):
            output_content.append(line)
            lastfind = False
            
        elif line.startswith('FCM:'):
            output_content.append(line)
            lastfind = False
            
        elif line[:3].strip().isdigit():  # Detecting EDL entries based on line starting with a number
            entry_number = line[:3].strip()
            if verbose:
                print("Event line found", entry_number)
            ccc_path = ccc_dict.get(entry_number)
            
            if ccc_path:
            
                if verbose:
                    print("Found match at", ccc_path)
            
                slope, offset, power, saturation = read_ccc_file(ccc_path)
                new_line = line
                output_content.append(new_line)
                new_line = f"*ASC_SOP ({' '.join(map(lambda x: f'{float(x):.6f}', slope))})"
                new_line += f"({ ' '.join(map(lambda x: f'{float(x):.6f}', offset))})"
                new_line += f"({ ' '.join(map(lambda x: f'{float(x):.6f}', power))})\n"
                new_line += f"*ASC_SAT {float(saturation):.6f}\n"
                output_content.append(new_line)

                
                if verbose:
                    print(new_line)
                lastfind = True
            else:
                if verbose:
                    print("[WARNING] No match found")
                    print(line)
                output_content.append(line)  # If no match found, just append the original line
                lastfind = False
        elif (line[:4].strip() == "*ASC") and lastfind:
            pass
        elif lastfind and (line != "\n"):
            output_content.insert(-1, line)
        else:
            output_content.append(line)  # Append other lines unchanged
            lastfind = False

    # Write to the output EDL file
    with open(output_path, 'w') as file:
        file.writelines(output_content)

def process_edl(edl, cccDict):
    # Example function to process the EDL file and CCC files
    print(f"Processing EDL: {edl}")
    output_file = f"{os.path.splitext(edl)[0]}_cdl.edl"
    write_output_edl(output_file, read_edl_file(edl), cccDict)
    return output_file

def main():
	
    parser = argparse.ArgumentParser(description="Converts EDL and CCCs to EDL with CDL values.")
    parser.add_argument('-e', '--edl', type=str, required=True, help='Input EDL file')
    parser.add_argument('-c', '--cccdir', type=str, required=True, help='Directory with CCC files')
    parser.add_argument('-v', '--verbose', action='store_true', help='Give verbose logging')
    parser.add_argument('-l', '--loose', action='store_true', help='Makes reel and ccc matching looser')
    parser.add_argument('-p', '--pattern', type=str, default='.ccc', required=False, help='Alternate file extension pattern for finding files, defaults to ".ccc"')
    
    args = parser.parse_args()
    global verbose
    global loose
    verbose = args.verbose
    loose = args.loose
    pattern = "*" + args.pattern
    
    # Expand glob patterns for cccdir and search for cccs
    if verbose:
	    print("Searching for", pattern, "in", str(args.cccdir))
    ccc_files = find_ccc_files(args.cccdir, args.edl, pattern)
    
    if len(ccc_files) < 1:
        print("[ERROR] No", pattern, "files found in the specified directory.")
        return
    
    output = process_edl(args.edl, ccc_files)
    print(f"Generated EDL CDL: {output}")

if __name__ == '__main__':
    main()
