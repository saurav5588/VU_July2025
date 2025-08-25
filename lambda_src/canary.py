import os, time, urllib.request, boto3

CLOUDWATCH_NS = os.environ.get("CW_NAMESPACE", "WebHealth")
URLS = [u.strip() for u in os.environ.get("URLS", "").split(",") if u.strip()]
if not URLS:
    URLS = [os.environ.get("TARGET_URL", "https://www.google.com")]
cw = boto3.client("cloudwatch")

def lambda_handler(event, context):
    results = []
    for url in URLS:
        start = time.time()
        ok = 0
        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                ok = 1 if r.status == 200 else 0
        except Exception:
            ok = 0
        latency = time.time() - start
        dims = [{"Name":"URL","Value":url}]
        cw.put_metric_data(
            Namespace=CLOUDWATCH_NS,
            MetricData=[
                {"MetricName":"Availability","Dimensions":dims,"Value":ok,"Unit":"Count"},
                {"MetricName":"Latency","Dimensions":dims,"Value":latency,"Unit":"Seconds"},
            ]
        )
        results.append({"url": url, "availability": ok, "latency_s": round(latency,3)})
    return results
