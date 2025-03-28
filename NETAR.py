import sys
from parse import process_dsl_to_xml

def main():
    """Main function to handle DSL processing."""
    input_file = "network.dsl"
    output_file = "final_output.xml"

    print("[INFO] Starting DSL to XML conversion...")

    try:
        process_dsl_to_xml(input_file, output_file)
        print(f"[INFO] Successfully generated XML: {output_file}")
    except Exception as e:
        print(f"[ERROR] Failed to process DSL file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
