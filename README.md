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

## References
[1] Benjamin Y. Chan and Elaine Shi. 2020. Streamlet: Textbook Streamlined
Blockchains. In Proceedings of the 2nd ACM Conference on Advances
in Financial Technologies (New York, NY, USA) (AFT ’20). 1–11.
https://doi.org/10.1145/3419614.3423256