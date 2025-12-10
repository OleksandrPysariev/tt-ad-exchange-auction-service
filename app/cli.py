import asyncio
import typer
from pathlib import Path

from app.commands.generate_auction_data import generate_auction_data
from app.commands.load_data import load_json_to_db

app = typer.Typer(
    name="auction-cli",
    help="CLI for Ad Exchange Auction Service",
    add_completion=False,
)


@app.command()
def generate_input_json(
    output: Path = typer.Option(
        Path("data.json"),
        "--output",
        "-o",
        help="Output path for the generated JSON file",
    ),
    supplies: int = typer.Option(
        10,
        "--supplies",
        "-s",
        help="Number of supplies to generate",
    ),
    bidders: int = typer.Option(
        12,
        "--bidders",
        "-b",
        help="Number of bidders to generate",
    ),
):
    """
    Generate input JSON file with supplies and bidders for the auction service.

    This creates a static database file according to the task specifications.
    """

    try:
        result = generate_auction_data(
            output_path=output,
            num_supplies=supplies,
            num_bidders=bidders,
        )

        typer.secho(f"[OK] Successfully generated {output}", fg=typer.colors.GREEN)
        typer.echo(f"  Supplies: {result['supplies_count']}")
        typer.echo(f"  Bidders: {result['bidders_count']}")

    except Exception as e:
        typer.secho(f"[ERROR] Error generating JSON: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


@app.command()
def load_data(
    input_file: Path = typer.Option(
        Path("data.json"),
        "--input",
        "-i",
        help="Path to JSON file to load into database",
    ),
):
    """
    Load data from JSON file into the database.

    Parses the JSON file and stores supplies and bidders into database tables.
    """
    if not input_file.exists():
        typer.secho(f"[ERROR] File not found: {input_file}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    try:
        result = asyncio.run(load_json_to_db(input_file))

        typer.secho(f"[OK] Successfully loaded data from {input_file}", fg=typer.colors.GREEN)
        typer.echo(f"  Supplies loaded: {result['supplies_count']}")
        typer.echo(f"  Bidders loaded: {result['bidders_count']}")

    except Exception as e:
        typer.secho(f"[ERROR] Error loading data: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
