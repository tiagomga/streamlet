# streamlet

## About this project
This project is currently being conducted at LASIGE (Faculty of Sciences
of the University of Lisbon).

Currently, a normal implementation of Streamlet is being developed. The
main goal of this work is to adapt the normal protocol to include trusted
components. With this technique, the resilience of the protocol may increase
by reducing the number of replicas from $3f + 1$ to $2f + 1$.

## What is Streamlet?
Streamlet [1] is a novel streamlined blockchain protocol introduced by
Benjamin Y. Chan and Elaine Shi. The authors present the protocol for
three different settings: (a) Byzantine fault tolerant in a partially
synchronous network, (b) Byzantine fault tolerant in a synchronous network,
and (c) crash fault tolerant in a partially synchronous network. The
model of interest is based on the first setting as its fault and timing
assumptions have a broader spectrum than the two other settings, which is
better suited for the ongoing work.

The protocol tolerates at most $f$ faults in a total of $3𝑓 + 1$ servers.
It is assumed that servers have synchronized clocks, and the protocol
advances in epochs that can have any defined duration. The whole protocol
runs in a *Propose-Vote* fashion, where, in each epoch, the leader proposes
a new block, and the replicas vote for the proposal.

## Initializing the application
### Dependencies
As of the moment, the only dependency used is the `cryptography` package for
performing cryptographic operations. It can be installed using the command:

```sh
pip install -r requirements.txt
```

### Execution
The application starts by executing a script (`run_linux.sh` or `run_macos.sh`
depending on the OS). The script will spawn 4 terminal windows, each
corresponding to a server. In this scenario, 1 Byzantine fault is being
tolerated out of 4 servers. However, every spawned server is honest and
does not deviate from the protocol.

> Upon starting the application, it will create a folder called `\blockchain`
> where the finalized chain will be stored.

The application can be executed by running the following command:

**Linux**
```sh
./run_linux.sh
```

**MacOS**
```sh
./run_macos.sh
```

## References
[1] Benjamin Y. Chan and Elaine Shi. 2020. Streamlet: Textbook Streamlined
Blockchains. In Proceedings of the 2nd ACM Conference on Advances
in Financial Technologies (New York, NY, USA) (AFT ’20). 1–11.
https://doi.org/10.1145/3419614.3423256