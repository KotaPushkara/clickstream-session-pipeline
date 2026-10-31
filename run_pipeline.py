import argparse
from src.pipeline import run_pipeline

def main():
    parser = argparse.ArgumentParser(description="Clickstream event-to-sessionization pipeline")
    parser.add_argument("--input", default="data/input/events.csv")
    parser.add_argument("--output-dir", default="data/output")
    parser.add_argument("--report-dir", default="data/reports")
    parser.add_argument("--gap-minutes", type=int, default=30)
    parser.add_argument("--publish-mysql", action="store_true")
    args = parser.parse_args()
    report = run_pipeline(args.input, args.output_dir, args.report_dir,
                          args.gap_minutes, args.publish_mysql)
    print(f"Run {report['run_id']} completed: {report['status']}")
    print(f"Input={report['input_rows']} Accepted={report['accepted_unique_rows']} "
          f"Duplicates={report['exact_duplicate_rows']} Rejected={report['rejected_rows']} "
          f"Sessions={report['session_rows']}")
    print(f"Elapsed: {report['elapsed_seconds']} seconds")

if __name__ == "__main__":
    main()
