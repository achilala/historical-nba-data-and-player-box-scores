import kagglehub

def main():
    # Download latest version
    path = kagglehub.dataset_download("eoinamoore/historical-nba-data-and-player-box-scores")
    print("Path to dataset files:", path)


if __name__ == "__main__":
    main()
