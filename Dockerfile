FROM wso2/wso2am:4.7.0@sha256:4de3aabbb11d16a1c00d122312503070ea8617e0829133cbcc83f35d6868b889
COPY --chown=wso2carbon:wso2 vendor/postgresql-42.7.14.jar /home/wso2carbon/wso2am-4.7.0/repository/components/lib/
