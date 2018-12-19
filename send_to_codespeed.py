#!/usr/bin/env python3

import argparse
import re
import sys
import requests


class ArgsCodespeed:
    url = None
    user = None
    pw = None
    env = None


def send_to_codespeed(*, bench_name, result, commit_id, executable='make', branch='master', lessisbetter=False, units_title='Percent', units='percent', description='', result_max=None, result_min=None):
    """
    Send a benchmark result to codespeed over HTTP.
    """
    data = {
        # Mandatory fields
        'commitid': commit_id,
        'branch': branch,
        'project': 'Bitcoin Core',
        'executable': executable,
        'benchmark': bench_name,
        'environment': ArgsCodespeed.env,
        'result_value': result,
        # Optional. Default is taken either from VCS integration or from
        # current date
        # 'revision_date': current_date,
        # 'result_date': current_date,  # Optional, default is current date
        # 'std_dev': std_dev,  # Optional. Default is blank
        'max': result_max,  # Optional. Default is blank
        'min': result_min,  # Optional. Default is blank
        # Ignored if bench_name already exists:
        'lessisbetter': lessisbetter,
        'units_title': units_title,
        'units': units,
        'description': description,
    }

    print("Attempting to send benchmark ({}, {}) to codespeed".format(bench_name, result))

    resp = requests.post(
        ArgsCodespeed.url + '/result/add/',
        data=data,
        auth=(ArgsCodespeed.user, ArgsCodespeed.pw),
    )

    if resp.status_code != 202:
        raise ValueError('Request to codespeed returned an error %s, the response is:\n%s' % (resp.status_code, resp.text))


def main():
    parser = argparse.ArgumentParser(description="Read the given coverage info file and send it to codespeed", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--codespeed_url", default='https://codespeed.bitcoinperf.com', help="The codespeed auth url")
    parser.add_argument("--codespeed_user", default='marco', help="The codespeed auth user")
    parser.add_argument("--codespeed_pass", default='pass?', help="The codespeed auth pass")
    parser.add_argument("--codespeed_env", default='drahtbot-coverage', help="The codespeed env name")

    parser.add_argument("file", help="coverage info file (html top level)")
    parser.add_argument("commit_id", help="The commit id the file was generated on")
    args = parser.parse_args()

    ArgsCodespeed.url = args.codespeed_url
    ArgsCodespeed.user = args.codespeed_user
    ArgsCodespeed.pw = args.codespeed_pass
    ArgsCodespeed.env = args.codespeed_env

    parsed_lines = 0
    parsed_fun = 0
    parsed_branch = 0

    with open(args.file, encoding='utf-8') as f:
        for l in f:
            if '_coverage.info</td>' in l:
                bench_name_base = l.split('_coverage.info</td>')[0].split('>')[-1]
                continue

            if '>Lines:</td>' in l:
                parsed_lines = 1
                continue
            if parsed_lines == 1:
                hit_lines = int(l.split('</td>')[0].split('>')[-1])
                parsed_lines += 1
                continue
            if parsed_lines == 2:
                total_lines = int(l.split('</td>')[0].split('>')[-1])
                parsed_lines += 1
                continue

            if '>Functions:</td>' in l:
                parsed_fun= 1
                continue
            if parsed_fun== 1:
                hit_fun = int(l.split('</td>')[0].split('>')[-1])
                parsed_fun+= 1
                continue
            if parsed_fun== 2:
                total_fun = int(l.split('</td>')[0].split('>')[-1])
                parsed_fun+= 1
                continue

            if '>Branches:</td>' in l:
                parsed_branch= 1
                continue
            if parsed_branch== 1:
                hit_branch = int(l.split('</td>')[0].split('>')[-1])
                parsed_branch+= 1
                continue
            if parsed_branch== 2:
                total_branch = int(l.split('</td>')[0].split('>')[-1])
                parsed_branch+= 1
                continue

            if parsed_branch== 2 and parsed_fun==2 and parsed_lines==2:
             break

    cov_lines= 100. * hit_lines / total_lines
    cov_fun= 100. * hit_fun / total_fun
    cov_branch= 100. * hit_branch / total_branch

    send_to_codespeed(bench_name=bench_name_base+'_cov.lines.hit', result=hit_lines, commit_id=args.commit_id, units_title='Count', units='count')
    send_to_codespeed(bench_name=bench_name_base+'_cov.lines.total', result=total_lines, commit_id=args.commit_id, units_title='Count', units='count')
    send_to_codespeed(bench_name=bench_name_base+'_cov.lines.perc', result=cov_lines, commit_id=args.commit_id, units_title='Coverage', units='percent')

    send_to_codespeed(bench_name=bench_name_base+'_cov.fun.hit', result=hit_fun, commit_id=args.commit_id, units_title='Count', units='count')
    send_to_codespeed(bench_name=bench_name_base+'_cov.fun.total', result=total_fun, commit_id=args.commit_id, units_title='Count', units='count')
    send_to_codespeed(bench_name=bench_name_base+'_cov.fun.perc', result=cov_fun, commit_id=args.commit_id,  units_title='Coverage', units='percent')

    send_to_codespeed(bench_name=bench_name_base+'_cov.branch.hit', result=hit_branch, commit_id=args.commit_id, units_title='Count', units='count')
    send_to_codespeed(bench_name=bench_name_base+'_cov.branch.total', result=total_branch, commit_id=args.commit_id, units_title='Count', units='count')
    send_to_codespeed(bench_name=bench_name_base+'_cov.branch.perc', result=cov_branch, commit_id=args.commit_id,  units_title='Coverage', units='percent')

if __name__ == "__main__":
    main()
