#!/usr/bin/env python3

import logging
from pathlib import Path

from graph.GraphSampler import GraphSampler
from .sample_profiles import parse_args
from .utils import plausible_checks_for_args

BASE = Path(__file__).stem
logger = logging.getLogger(BASE)


def prepare_and_sample_from_kg(args, n_already_sampled, outfile):
    p = Path(args.save_dir)
    p.mkdir(parents=True, exist_ok=True)

    kg = GraphSampler(args)
    kg.load(args)
    logger.debug(kg)

    p = kg.get_distance_map_path()

    if p.exists():
        kg.load_map_and_check(p.resolve())
        # ~ print(kg.distance_map[0,:])
        # ~ print(kg.distance_map)
    else:
        kg.get_distance_map()
        # ~ print(kg.distance_map)

    if not p.exists():
        kg.save(p.resolve())

    hist, min_dist_nonzero, max_dist_nonzero = kg.dist_hist()

    logger.info("  sampling ego-network based profiles")
    # sample items from item ego-networks
    # modeling people who are rather focused on a particular topic
    min_plausible_dist = kg.get_min_plausible_dist(args.n_interact_max)
    if min_plausible_dist < 0:
        min_plausible_dist = max_dist_nonzero
    for i in range(args.n_within_range):
        only_zeros = True
        while only_zeros:
            # sample a random item
            items = kg.sample_n_items(args.n_within_range)
            for item in items:
                # look around the range-neighborhood of that random item. zero range doesn't make sense as there is a >= check inside
                ids = kg.get_items_in_range(
                    item, nw_range_min=1, nw_range_max=min_plausible_dist + 1
                )
                if len(ids) > 0:
                    logger.debug(f"    {i}th profile egn")
                    only_zeros = False
                    n_already_sampled += 1
                    for j, _id in enumerate(ids):
                        print(f"{i}\t{_id}\t{j}", file=outfile)
                    break

    logger.info("  sampling path-based profiles")
    # sample items from item paths
    # modeling people who are rather focused on a particular topic
    for i in range(n_already_sampled, args.n_along_path + n_already_sampled):
        only_zeros = True
        while only_zeros:
            # sample random items
            items = kg.sample_n_items(args.n_along_path)
            for item in items:
                path = kg.sample_path_of_len(
                    item,
                    args.n_interact_max,
                    min_dist_nonzero,
                    max_dist_nonzero,
                    unique_path=True,
                )
                if len(path) >= args.n_interact_min:
                    logger.debug(f"    {n_already_sampled}th profile pth")
                    only_zeros = False
                    n_already_sampled += 1
                    for j, _id in enumerate(path):
                        print(f"{i}\t{_id}\t{j}", file=outfile)
                    break

    logger.info("  sampling remaining random profiles")
    if args.n_rand > 0:
        # sample random items
        for i in range(n_already_sampled, args.n_rand + n_already_sampled):
            # sample random items
            items = kg.sample_n_items(args.n_interact_max)
            if len(items) > args.n_interact_min:
                n_already_sampled += 1
                for j, _id in enumerate(ids):
                    print(f"{i}\t{_id}\t{j}", file=outfile)
                break
    return n_already_sampled


def main(args):
    if args.interactions_file is not None:
        raise Exception(
            "Unplausible. interactions_sampler can only sample interactions file that you just provided...!"
        )

    args = plausible_checks_for_args(args, False, 0)
    logger.info(args)

    n_already_sampled = 0

    try:
        with open(Path(args.save_dir, "user_interactions.tsv"), "w") as _out:
            print("wisski_user\twisski_item\tat", file=_out)
            logger.info("sampling KG-informed profiles now")
            n_already_sampled = prepare_and_sample_from_kg(
                args, n_already_sampled, _out
            )
            logger.info("sampling KG-informed profiles done")
    except:
        Path(args.save_dir, "user_interactions.tsv").unlink(missing_ok=True)
        logger.warning("an error occurred. removed user_interactions.tsv")
        return
    logger.info(f"done sampling {n_already_sampled} user profiles in total")


if __name__ == "__main__":
    args = parse_args()

    configure_logging(args, BASE)

    main(args)
