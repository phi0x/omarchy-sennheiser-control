/* SDP discovery only; no pairing, settings, or audio changes. */
#include <stdio.h>
#include <bluetooth/bluetooth.h>
#include <bluetooth/sdp.h>
#include <bluetooth/sdp_lib.h>
int main(int argc, char **argv) {
    bdaddr_t remote;
    if (argc != 2 || str2ba(argv[1], &remote)) return 2;
    sdp_session_t *session = sdp_connect(BDADDR_ANY, &remote, SDP_RETRY_IF_BUSY);
    if (!session) { perror("SDP connection"); return 1; }
    uint8_t bytes[] = {0xa2,0x12,0x9f,0xf3,0x08,0x1b,0x4c,0x45,0x8a,0xfe,0x46,0x9d,0x9c,0x48,0x42,0xec};
    uuid_t uuid;
    sdp_uuid128_create(&uuid, bytes);
    uint32_t range = 0x0000ffff;
    sdp_list_t *search = sdp_list_append(NULL, &uuid);
    sdp_list_t *attrs = sdp_list_append(NULL, &range), *records = NULL;
    int channel = 0;
    if (sdp_service_search_attr_req(session, search, SDP_ATTR_REQ_RANGE, attrs, &records) == 0) {
        for (sdp_list_t *p = records; p; p = p->next) {
            sdp_list_t *protocols = NULL;
            if (sdp_get_access_protos(p->data, &protocols) == 0) {
                int port = sdp_get_proto_port(protocols, RFCOMM_UUID);
                if (port > 0 && port <= 30) channel = port;
                for (sdp_list_t *q = protocols; q; q = q->next) sdp_list_free(q->data, NULL);
                sdp_list_free(protocols, NULL);
            }
        }
    }
    sdp_list_free(records, (sdp_free_func_t)sdp_record_free);
    sdp_list_free(search, NULL); sdp_list_free(attrs, NULL); sdp_close(session);
    if (!channel) { fprintf(stderr, "HDB 630 control service not found\n"); return 1; }
    printf("%d\n", channel);
    return 0;
}
