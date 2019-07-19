#include <iostream>
#include <pcap.h>

using namespace std;

static int packetCount = 0;

FILE* output = fopen("out.txt","w+");


void packetHandler(u_char *userData, const struct pcap_pkthdr* pkthdr, const u_char* packet) {
  fprintf(output,"%s\n",&pkthdr);
}

int main() {
  char *dev;
  pcap_t *descr;
  char errbuf[PCAP_ERRBUF_SIZE];

  dev = pcap_lookupdev(errbuf);
  if (dev == NULL) {
      cout << "pcap_lookupdev() failed: " << errbuf << endl;
      return 1;
  }

  descr = pcap_open_live(dev, BUFSIZ, 0, -1, errbuf);
  if (descr == NULL) {
      cout << "pcap_open_live() failed: " << errbuf << endl;
      return 1;
  }

  if (pcap_loop(descr, 10, packetHandler, NULL) < 0) {
      cout << "pcap_loop() failed: " << pcap_geterr(descr);
      return 1;
  }

  cout << "capture finished" << endl;

  return 0;
}
