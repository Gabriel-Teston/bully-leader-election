FROM hashicorp/terraform:latest

RUN apk --no-cache add curl bash which python3
RUN curl -sSL https://sdk.cloud.google.com > /tmp/gcl && bash /tmp/gcl --install-dir=~/gcloud --disable-prompts

ENV PATH $PATH:~/gcloud/google-cloud-sdk/bin